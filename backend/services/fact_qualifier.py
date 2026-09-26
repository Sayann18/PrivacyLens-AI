from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

from models.analysis_v2 import Ambiguity, Evidence, Fact, Gap
from models.enums import Confidence, DisclosureStatus, FactCategory, Importance
from models.normalized_document import NormalizedDocument
from models.qualification import FactQualification, QualificationDisposition


@dataclass(frozen=True)
class _Decision:
    disposition: QualificationDisposition
    reason: str
    triggers: tuple[str, ...] = ()
    modifiers: tuple[str, ...] = ()
    importance: Importance = Importance.LOW


def max_importance(left: Importance, right: Importance) -> Importance:
    order = {Importance.LOW: 0, Importance.MEDIUM: 1, Importance.HIGH: 2}
    return left if order[left] >= order[right] else right


class FactQualifier:

    DOMAIN_BY_CATEGORY = {
        FactCategory.DATA_COLLECTION: "privacy",
        FactCategory.DATA_SHARING: "privacy",
        FactCategory.DATA_USAGE: "privacy",
        FactCategory.TRACKING: "privacy",
        FactCategory.ADVERTISING: "privacy",
        FactCategory.AI_USAGE: "privacy",
        FactCategory.RETENTION: "privacy",
        FactCategory.DELETION: "privacy",
        FactCategory.SUBSCRIPTION: "financial",
        FactCategory.AUTO_RENEWAL: "financial",
        FactCategory.TRIAL: "financial",
        FactCategory.FEE: "financial",
        FactCategory.REFUND: "financial",
        FactCategory.CANCELLATION: "financial",
        FactCategory.ARBITRATION: "contract",
        FactCategory.LIABILITY: "contract",
        FactCategory.TERMINATION: "contract",
        FactCategory.CONTENT_LICENSE: "contract",
        FactCategory.GOVERNING_LAW: "contract",
    }

    _NEGATION_RE = re.compile(
        r"\b(?:do|does|did|will|would|can|could|may|shall|should|must)\s+not\b"
        r"|\bnever\b|\bno\s+(?:sale|sales|sharing|sharing of|disclosure)\b"
        r"|\bwithout\s+(?:selling|sharing|disclosing)\b",
        re.I,
    )

    _PRICE_RE = re.compile(r"(?:[$€£₹]\s?\d+(?:[,.]\d{1,2})?|\b\d+(?:[,.]\d{1,2})?\s?(?:USD|EUR|GBP|INR)\b)", re.I)
    _TIMEBOUND_RE = re.compile(r"\b\d+\s*(?:day|days|week|weeks|month|months|year|years|hour|hours)\b|\b(?:daily|weekly|monthly|quarterly|annual|yearly)\b", re.I)

    _SERVICE_PROVIDER = re.compile(r"\b(?:service providers?|vendors?|hosting providers?|contractors?)\b", re.I)
    _ADVERTISING_RECIPIENT = re.compile(r"\b(?:advertisers?|advertising partners?|ad networks?)\b", re.I)
    _UNSPECIFIED_RECIPIENT = re.compile(r"\b(?:certain partners?|other parties|selected partners?|other third parties|certain third parties)\b", re.I)
    _SALE_RE = re.compile(r"\b(?:sell|sale|sales|monetiz(?:e|ation))\b", re.I)
    _TARGETED_RE = re.compile(r"\b(?:targeted|personalized|behavio(?:u)?ral)\s+advert", re.I)
    _CROSS_CONTEXT_TRACKING_RE = re.compile(r"\b(?:cross[- ]site|cross[- ]app|across (?:websites|services|devices)|fingerprint(?:ing)?|follow you across)\b", re.I)
    _BROAD_SCOPE_RE = re.compile(r"\b(?:including but not limited to|other (?:information|data|purposes|parties)|may include|as necessary|as appropriate|at our discretion|from time to time)\b", re.I)
    _NO_NOTICE_RE = re.compile(r"\b(?:without notice|without prior notice)\b", re.I)
    _DISCRETION_RE = re.compile(r"\b(?:at our discretion|at our sole discretion|in our discretion|as we determine|for any reason)\b", re.I)
    _SHORT_DEADLINE_RE = re.compile(r"\b(?:within|at least|no later than)\s*(?:\d+)\s*(?:day|days|hour|hours)\b|\b\d+\s*days?\s*(?:before|prior to)\b", re.I)

    _SENSITIVE = re.compile(
        r"\b(?:health|medical|biometric|genetic|precise location|financial information|payment information|identity document|government id|religion|sexual orientation|racial|ethnic|children(?:'s)? information)\b",
        re.I,
    )

    def _text(self, fact: Fact, evidence: Mapping[str, Evidence] | None = None) -> str:
        parts = [fact.object_, fact.purpose, fact.recipient, fact.conditions, fact.frequency, fact.duration]
        if evidence:
            parts.extend(evidence[eid].exact_quote for eid in fact.evidence_ids if eid in evidence)
        return " ".join(str(p) for p in parts if p).strip()

    @classmethod
    def _has_negation(cls, text: str) -> bool:
        return bool(cls._NEGATION_RE.search(text))

    @staticmethod
    def _confidence(fact: Fact) -> Confidence:
        if fact.confidence >= 0.85:
            return Confidence.HIGH
        if fact.confidence >= 0.60:
            return Confidence.MEDIUM
        return Confidence.LOW

    @classmethod
    def _is_material_condition(cls, text: str) -> tuple[bool, list[str]]:
        triggers: list[str] = []
        if cls._NO_NOTICE_RE.search(text):
            triggers.append("without_notice")
        if cls._DISCRETION_RE.search(text):
            triggers.append("discretionary")
        if cls._SHORT_DEADLINE_RE.search(text):
            triggers.append("time_sensitive")
        if cls._BROAD_SCOPE_RE.search(text):
            triggers.append("broad_or_open_ended_scope")
        return bool(triggers), triggers

    def _privacy(self, fact: Fact, text: str) -> _Decision:
        category = fact.category
        material, material_triggers = self._is_material_condition(text)
        lower = text.lower()

        if category == FactCategory.DATA_COLLECTION:
            if self._has_negation(lower) and any(v in lower for v in ("collect", "gather", "obtain")):
                return _Decision(QualificationDisposition.INFORMATIONAL, "The clause explicitly limits or denies collection in the supplied wording.", ("negation",), importance=Importance.LOW)
            sensitive = bool(self._SENSITIVE.search(text))
            marketing = bool(re.search(r"\b(?:advertis\w*|marketing|promotional)\b", lower))
            if sensitive and marketing:
                return _Decision(QualificationDisposition.ATTENTION, "Sensitive information is described in connection with advertising or marketing use.", ("sensitive_data", "marketing_purpose"), ("meaningful_user_consequence",), importance=Importance.HIGH)
            if material:
                return _Decision(QualificationDisposition.AMBIGUOUS, "The scope or conditions of the collection are not fully defined in the supplied wording.", tuple(material_triggers), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The clause clearly describes information the service says it collects.", ("ordinary_collection",), importance=Importance.LOW)

        if category == FactCategory.DATA_SHARING:
            if self._has_negation(lower) and ("share" in lower or self._SALE_RE.search(lower)):
                return _Decision(QualificationDisposition.INFORMATIONAL, "The clause explicitly limits or denies sharing or sale in the supplied wording.", ("negation",), importance=Importance.LOW)
            if self._UNSPECIFIED_RECIPIENT.search(text):
                return _Decision(QualificationDisposition.AMBIGUOUS, "The recipients are described broadly without clearly identifying who is covered.", ("unspecified_recipients",), importance=Importance.MEDIUM)
            if self._SALE_RE.search(text) or self._ADVERTISING_RECIPIENT.search(text):
                triggers = ["sale_or_monetization"] if self._SALE_RE.search(text) else []
                if self._ADVERTISING_RECIPIENT.search(text):
                    triggers.append("advertising_recipient")
                return _Decision(QualificationDisposition.ATTENTION, "The document describes sharing or monetization that may extend beyond routine service operation.", tuple(triggers), ("third_party_scope",), importance=Importance.HIGH if self._SENSITIVE.search(text) else Importance.MEDIUM)
            if self._SERVICE_PROVIDER.search(text):
                return _Decision(QualificationDisposition.INFORMATIONAL, "The clause identifies service providers involved in operating the service.", ("service_provider",), importance=Importance.LOW)
            if "third part" in lower or "affiliate" in lower or "partner" in lower:
                return _Decision(QualificationDisposition.AMBIGUOUS, "The clause identifies third-party sharing but does not clearly define the recipient scope.", ("broad_third_party_scope",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes a sharing or disclosure practice.", ("disclosure",), importance=Importance.LOW)

        if category == FactCategory.DATA_USAGE:
            if material:
                return _Decision(QualificationDisposition.AMBIGUOUS, "The stated use includes broad or discretionary wording that leaves scope less specific.", tuple(material_triggers), importance=Importance.MEDIUM)
            if self._TARGETED_RE.search(text) or re.search(r"\b(?:use|process)\b.{0,80}\b(?:for advertising|for marketing)\b", lower):
                return _Decision(QualificationDisposition.ATTENTION, "The document connects information use with targeted or personalized advertising.", ("advertising_purpose",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The clause describes a stated purpose for using information.", ("stated_purpose",), importance=Importance.LOW)

        if category == FactCategory.TRACKING:
            if self._CROSS_CONTEXT_TRACKING_RE.search(text) or self._TARGETED_RE.search(text) or re.search(r"\btracking\b.{0,100}\b(?:advertis|marketing|profil)\b", lower):
                return _Decision(QualificationDisposition.ATTENTION, "The tracking description includes cross-context tracking, profiling, or targeted advertising.", ("meaningful_tracking_scope",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes cookies, analytics, or similar technologies without a material concern in the supplied wording.", ("ordinary_tracking_disclosure",), importance=Importance.LOW)

        if category == FactCategory.ADVERTISING:
            if self._TARGETED_RE.search(text) or self._ADVERTISING_RECIPIENT.search(text):
                return _Decision(QualificationDisposition.ATTENTION, "The advertising clause includes personalization, targeting, or third-party advertising involvement.", ("targeted_or_third_party_ads",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document discloses ordinary advertising or marketing activity.", ("ordinary_advertising",), importance=Importance.LOW)

        if category == FactCategory.AI_USAGE:
            training = bool(re.search(r"\b(?:train|training|improve|fine[- ]?tune)\b.{0,120}\b(?:data|information|content|conversations?|prompts?|models?)\b", lower))
            if training and not self._has_negation(lower):
                return _Decision(QualificationDisposition.ATTENTION, "The document describes using user-provided content or information for AI/model improvement.", ("model_training",), importance=Importance.HIGH)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes AI-assisted functionality without stating that user data is used for model training in this clause.", ("ai_functionality",), importance=Importance.LOW)

        if category == FactCategory.RETENTION:
            if self._has_negation(lower) and "retain" in lower:
                return _Decision(QualificationDisposition.INFORMATIONAL, "The clause explicitly limits or denies retention in the supplied wording.", ("negation",), importance=Importance.LOW)
            if re.search(r"\b(?:indefinitely|forever|without a defined period)\b", lower):
                return _Decision(QualificationDisposition.ATTENTION, "The document describes retention without a defined end point.", ("indefinite_retention",), importance=Importance.MEDIUM)
            if re.search(r"\b(?:as long as necessary|as required|as appropriate|as needed)\b", lower):
                return _Decision(QualificationDisposition.AMBIGUOUS, "The retention period is described using open-ended wording rather than a defined timeframe or criterion.", ("open_ended_retention",), importance=Importance.MEDIUM)
            if self._TIMEBOUND_RE.search(text):
                return _Decision(QualificationDisposition.INFORMATIONAL, "The document states a defined retention period or cadence.", ("defined_retention_period",), importance=Importance.LOW)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes a retention practice.", ("retention_disclosed",), importance=Importance.LOW)

        if category == FactCategory.DELETION:
            if any(p in lower for p in ("request deletion", "delete your account", "delete your data", "delete through", "account settings")) and not material:
                return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes a deletion or erasure mechanism.", ("deletion_mechanism",), importance=Importance.LOW)
            if material or re.search(r"\b(?:may retain|cannot delete|not eligible|subject to exceptions)\b", lower):
                return _Decision(QualificationDisposition.ATTENTION, "The deletion clause includes conditions or limitations that may affect the user's ability to remove information.", tuple(material_triggers) or ("deletion_limitation",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes deletion or erasure of information or an account.", ("deletion",), importance=Importance.LOW)

        return _Decision(QualificationDisposition.INFORMATIONAL, "The clause is relevant to privacy but is not independently concerning based on the supplied wording.")

    def _financial(self, fact: Fact, text: str) -> _Decision:
        lower = text.lower()
        category = fact.category
        material, material_triggers = self._is_material_condition(text)

        if category == FactCategory.FEE:
            concerning = bool(re.search(r"\b(?:additional|extra|service|processing|convenience|surcharge|late)\s+(?:fee|fees|charge|charges)\b", lower)) or bool(re.search(r"\b(?:fee|charge)\b.{0,60}\b(?:may apply|may vary|at our discretion)\b", lower))
            price_change = bool(re.search(r"\b(?:price|prices|pricing)\b.{0,60}\b(?:may change|change at any time|without notice)\b", lower))
            if self._has_negation(lower) and re.search(r"\b(?:fee|charge|price)\b", lower) and not concerning and not price_change:
                return _Decision(QualificationDisposition.INFORMATIONAL, "The clause explicitly limits or denies the stated fee or charge.", ("negation",), importance=Importance.LOW)
            if concerning or price_change:
                triggers = []
                if concerning:
                    triggers.append("additional_or_conditional_charge")
                if price_change:
                    triggers.append("price_change")
                return _Decision(QualificationDisposition.ATTENTION, "The payment wording introduces an additional, conditional, or changeable charge beyond a straightforward listed price.", tuple(triggers), importance=Importance.MEDIUM)
            if self._PRICE_RE.search(text) or re.search(r"\b(?:monthly|annual|yearly|weekly|billing cycle|billing period|per month|per year)\b", lower):
                return _Decision(QualificationDisposition.INFORMATIONAL, "The clause states an ordinary disclosed price or billing frequency.", ("ordinary_price_or_billing",), importance=Importance.LOW)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document states a financial term without a material additional condition in the supplied wording.", ("ordinary_financial_term",), importance=Importance.LOW)

        if category == FactCategory.AUTO_RENEWAL:
            explicit_auto = bool(re.search(r"\b(?:automatically renew|auto[- ]renew|automatically renews|recurring charge|recurring billing)\b", lower))
            deadline = bool(re.search(r"\b\d+\s*days?\s*(?:before|prior to)\b", lower))
            paid = bool(re.search(r"\b(?:charge|charged|billing|payment|paid)\b", lower))
            if explicit_auto and (deadline or paid):
                triggers = ["automatic_renewal"] + (["cancellation_deadline"] if deadline else []) + (["recurring_payment"] if paid else [])
                return _Decision(QualificationDisposition.ATTENTION, "The subscription includes automatic renewal with a payment or timing condition.", tuple(triggers), importance=Importance.MEDIUM)
            if explicit_auto:
                return _Decision(QualificationDisposition.ATTENTION, "The document states that the subscription renews automatically.", ("automatic_renewal",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document refers to renewal without stating an additional material condition.", ("renewal_reference",), importance=Importance.LOW)

        if category == FactCategory.TRIAL:
            conversion = bool(re.search(r"\b(?:automatically|will)\b.{0,60}\b(?:charge|charged|paid|convert|converts|converted)\b", lower))
            if conversion:
                return _Decision(QualificationDisposition.ATTENTION, "The trial includes an automatic or stated transition to paid service.", ("trial_to_paid",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The clause describes a trial period without a stated payment consequence in the supplied wording.", ("trial_period",), importance=Importance.LOW)

        if category == FactCategory.SUBSCRIPTION:
            commitment = bool(re.search(r"\b(?:minimum\s+(?:term|commitment)|annual commitment|non-cancellable|cannot cancel|committed term|minimum\s+\d+[- ]month(?:s)?\s+commitment)\b", lower))
            if commitment:
                return _Decision(QualificationDisposition.ATTENTION, "The subscription includes a commitment or cancellation restriction.", ("commitment_or_restriction",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document identifies a subscription or service plan.", ("subscription_exists",), importance=Importance.LOW)

        if category == FactCategory.CANCELLATION:
            deadline = bool(re.search(r"\b(?:days? before|prior to renewal|deadline|advance notice|notice of cancellation|cancel at least)\b", lower))
            constrained = bool(re.search(r"\b(?:must cancel by|only by|only through|contact support|call us|email us|cannot cancel online)\b", lower))
            if deadline or constrained or material:
                triggers = []
                if deadline:
                    triggers.append("cancellation_deadline")
                if constrained:
                    triggers.append("restricted_cancellation_method")
                triggers.extend(t for t in material_triggers if t not in triggers)
                return _Decision(QualificationDisposition.ATTENTION, "The cancellation clause includes a deadline, restricted process, or other condition that may affect when cancellation takes effect.", tuple(triggers), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes how a user can cancel or terminate the service.", ("cancellation_process",), importance=Importance.LOW)

        if category == FactCategory.REFUND:
            non_ref = bool(re.search(r"\b(?:non[- ]refundable|no refunds?|all sales are final)\b", lower))
            restrictive = bool(re.search(r"\b(?:only if|except|excludes|not eligible|store credit only)\b", lower))
            explicit_window = bool(self._TIMEBOUND_RE.search(text) and re.search(r"\brefund", lower))
            if non_ref or restrictive:
                triggers = (["non_refundable"] if non_ref else []) + (["refund_restrictions"] if restrictive else [])
                return _Decision(QualificationDisposition.ATTENTION, "The refund clause includes a stated exclusion or restriction that may affect the user's payment recovery options.", tuple(triggers), importance=Importance.MEDIUM)
            if explicit_window:
                return _Decision(QualificationDisposition.INFORMATIONAL, "The document states a defined refund rule or timeframe.", ("defined_refund_rule",), importance=Importance.LOW)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes a refund or reimbursement policy.", ("refund_policy",), importance=Importance.LOW)

        return _Decision(QualificationDisposition.INFORMATIONAL, "The financial clause is a disclosed term without a material attention trigger in the supplied wording.")

    def _contract(self, fact: Fact, text: str) -> _Decision:
        lower = text.lower()
        category = fact.category
        material, material_triggers = self._is_material_condition(text)

        if category == FactCategory.ARBITRATION:
            if re.search(r"\b(?:class action|class-action)\b", lower):
                return _Decision(QualificationDisposition.ATTENTION, "The agreement includes a class-action limitation alongside dispute-related wording.", ("class_action_waiver",), importance=Importance.HIGH)
            if re.search(r"\bbinding arbitration\b", lower):
                return _Decision(QualificationDisposition.ATTENTION, "The agreement requires certain disputes to be resolved through binding arbitration.", ("binding_arbitration",), importance=Importance.MEDIUM)
            if re.search(r"\barbitration\b", lower):
                return _Decision(QualificationDisposition.ATTENTION, "The agreement describes arbitration as part of its dispute process.", ("arbitration",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document refers to dispute resolution without an additional material limitation in the supplied wording.", ("dispute_resolution",), importance=Importance.LOW)

        if category == FactCategory.LIABILITY:
            indemnification = bool(re.search(r"\b(?:indemnif|hold harmless|defend and indemnify|reimburse for claims)\b", lower))
            limitation = bool(re.search(r"\b(?:limitation of liability|liability is limited|liability shall not exceed|not liable|no liability|exclude(?:s|d)? (?:all|any)|consequential damages|liability cap)\b", lower))
            if indemnification:
                return _Decision(QualificationDisposition.ATTENTION, "The agreement places an indemnification or hold-harmless obligation on a party.", ("indemnification",), importance=Importance.MEDIUM)
            if limitation:
                return _Decision(QualificationDisposition.ATTENTION, "The agreement limits liability or excludes certain categories of damages.", ("liability_limitation",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document mentions liability without a material limitation trigger in the supplied wording.", ("liability_reference",), importance=Importance.LOW)

        if category == FactCategory.TERMINATION:
            if re.search(r"\b(?:change|modify|update)\s+(?:these|the)\s+terms\b", lower):
                broad = bool(self._DISCRETION_RE.search(text) or self._NO_NOTICE_RE.search(text) or re.search(r"\bfor any reason\b", lower))
                if broad:
                    return _Decision(QualificationDisposition.ATTENTION, "The agreement allows its terms to be changed under broad or limited-notice conditions.", ("unilateral_changes",), importance=Importance.MEDIUM)
                return _Decision(QualificationDisposition.INFORMATIONAL, "The agreement describes a process for updating its terms.", ("terms_update",), importance=Importance.LOW)
            user_closure = bool(re.search(r"\byou\s+(?:may|can)\s+(?:close|terminate|cancel)\b", lower))
            company_action = bool(re.search(r"\b(?:we|company|service)\b.{0,80}\b(?:terminate|suspend|disable)\b", lower))
            broad = bool(self._DISCRETION_RE.search(text) or self._NO_NOTICE_RE.search(text) or re.search(r"\bfor any reason\b", lower))
            if company_action and (broad or material):
                triggers = ["company_termination_or_suspension"]
                triggers.extend(t for t in material_triggers if t not in triggers)
                return _Decision(QualificationDisposition.ATTENTION, "The service reserves termination or suspension powers subject to broad or limited-notice conditions.", tuple(triggers), importance=Importance.MEDIUM)
            if user_closure and not company_action:
                return _Decision(QualificationDisposition.INFORMATIONAL, "The agreement describes an ordinary account-closing or termination option for the user.", ("user_termination_option",), importance=Importance.LOW)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The agreement describes termination or suspension without a material attention trigger in the supplied wording.", ("termination_reference",), importance=Importance.LOW)

        if category == FactCategory.CONTENT_LICENSE:
            user_grant = bool(re.search(r"\byou\s+(?:grant|give)\b.{0,100}\blicen[sc]e\b", lower))
            broad = bool(re.search(r"\b(?:worldwide|perpetual|irrevocable|transferable|sublicensable|royalty[- ]free)\b", lower))
            if user_grant and broad:
                return _Decision(QualificationDisposition.ATTENTION, "The agreement grants the company broad rights to use submitted content.", ("broad_user_content_license",), importance=Importance.HIGH)
            if user_grant:
                return _Decision(QualificationDisposition.ATTENTION, "The agreement grants the company a license to use user-provided content.", ("user_content_license",), importance=Importance.MEDIUM)
            return _Decision(QualificationDisposition.INFORMATIONAL, "The document describes a content license without a broad user-content grant in the supplied wording.", ("license_reference",), importance=Importance.LOW)

        if category == FactCategory.GOVERNING_LAW:
            return _Decision(QualificationDisposition.INFORMATIONAL, "The agreement identifies the governing law or jurisdiction.", ("governing_law",), importance=Importance.LOW)

        return _Decision(QualificationDisposition.INFORMATIONAL, "The contract clause is disclosed without a material attention trigger in the supplied wording.")

    def qualify_fact(self, fact: Fact, evidence: Mapping[str, Evidence] | None = None) -> FactQualification:
        text = self._text(fact, evidence)
        confidence = self._confidence(fact)
        evidence_ids = list(fact.evidence_ids)

        if fact.status == DisclosureStatus.CONFLICTING:
            decision = _Decision(QualificationDisposition.CONFLICTING, "The fact is explicitly marked as conflicting by the upstream analysis.", ("upstream_conflict",), importance=Importance.MEDIUM)
        elif fact.status == DisclosureStatus.AMBIGUOUS:
            decision = _Decision(QualificationDisposition.AMBIGUOUS, "The fact is explicitly marked as ambiguous by the upstream analysis.", ("upstream_ambiguity",), importance=Importance.MEDIUM)
        elif fact.category in {
            FactCategory.DATA_COLLECTION, FactCategory.DATA_SHARING, FactCategory.DATA_USAGE,
            FactCategory.TRACKING, FactCategory.ADVERTISING, FactCategory.AI_USAGE,
            FactCategory.RETENTION, FactCategory.DELETION,
        }:
            decision = self._privacy(fact, text)
        elif fact.category in {
            FactCategory.SUBSCRIPTION, FactCategory.AUTO_RENEWAL, FactCategory.TRIAL,
            FactCategory.FEE, FactCategory.REFUND, FactCategory.CANCELLATION,
        }:
            decision = self._financial(fact, text)
        else:
            decision = self._contract(fact, text)

        should_surface = decision.disposition in {
            QualificationDisposition.ATTENTION,
            QualificationDisposition.AMBIGUOUS,
            QualificationDisposition.CONFLICTING,
        } and bool(evidence_ids)

        
        
        if should_surface and confidence == Confidence.LOW:
            should_surface = False

        domain = self.DOMAIN_BY_CATEGORY.get(fact.category, "other")
        return FactQualification(
            fact_id=fact.fact_id,
            domain=domain,
            category=fact.category.value,
            disposition=decision.disposition,
            should_surface=should_surface,
            importance=decision.importance,
            confidence=confidence,
            reason=decision.reason,
            triggers=list(decision.triggers),
            modifiers=list(decision.modifiers),
            evidence_ids=evidence_ids,
        )

    def qualify(self, facts: Iterable[Fact], evidence: Iterable[Evidence] | None = None) -> list[FactQualification]:
        fact_list = list(facts)
        evidence_map = {item.evidence_id: item for item in (evidence or [])}
        results = [self.qualify_fact(fact, evidence_map) for fact in fact_list]

        
        by_id = {result.fact_id: result for result in results}
        categories = {fact.category for fact in fact_list}
        if FactCategory.AUTO_RENEWAL in categories and FactCategory.CANCELLATION in categories:
            for fact in fact_list:
                if fact.category in {FactCategory.AUTO_RENEWAL, FactCategory.CANCELLATION}:
                    current = by_id[fact.fact_id]
                    if current.should_surface and current.disposition == QualificationDisposition.ATTENTION:
                        by_id[fact.fact_id] = current.model_copy(update={
                            "importance": Importance.HIGH,
                            "modifiers": list(dict.fromkeys(current.modifiers + ["compound_payment_condition"])),
                            "reason": current.reason + " The document also contains a related cancellation condition.",
                        })

        
        
        if FactCategory.DATA_SHARING in categories and FactCategory.ADVERTISING in categories:
            for result in list(by_id.values()):
                if result.category in {FactCategory.DATA_SHARING.value, FactCategory.ADVERTISING.value} and result.should_surface:
                    by_id[result.fact_id] = result.model_copy(update={
                        "importance": max_importance(result.importance, Importance.HIGH),
                        "modifiers": list(dict.fromkeys(result.modifiers + ["sharing_plus_advertising"])),
                    })

        if FactCategory.AI_USAGE in categories and FactCategory.DATA_COLLECTION in categories:
            for result in list(by_id.values()):
                if result.category in {FactCategory.AI_USAGE.value, FactCategory.DATA_COLLECTION.value} and result.should_surface:
                    by_id[result.fact_id] = result.model_copy(update={
                        "modifiers": list(dict.fromkeys(result.modifiers + ["ai_plus_collection"])),
                    })

        return [by_id[result.fact_id] for result in results]

    @staticmethod
    def relevant_gap(gap: Gap, document: NormalizedDocument) -> bool:
        text = document.raw_text.lower()
        label = gap.category.lower()
        privacy_signals = ("privacy", "personal data", "personal information", "we collect", "cookies", "data sharing")
        financial_signals = ("subscription", "billing", "payment", "price", "refund", "trial", "renew", "charge")
        if label == "retention period":
            return any(s in text for s in privacy_signals)
        if label == "third-party categories":
            return any(s in text for s in privacy_signals)
        if label == "cancellation process":
            return any(s in text for s in financial_signals)
        if label == "refund terms":
            return any(s in text for s in financial_signals)
        return False
