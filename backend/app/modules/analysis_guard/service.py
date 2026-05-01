from app.infrastructure.cache import build_cache_key
from app.modules.analysis_guard.schemas import AnalysisCacheIdentity, GeminiCallDecision


class AnalysisGuardService:
    def build_analysis_cache_key(self, identity: AnalysisCacheIdentity) -> str:
        return build_cache_key(
            (
                identity.normalized_input_text,
                identity.analysis_type,
                identity.persona_mode,
                ",".join(sorted(identity.evidence_chunk_ids)),
                identity.prompt_version,
                identity.model_version,
            )
        )

    def decide_gemini_call(
        self,
        identity: AnalysisCacheIdentity,
        *,
        has_sufficient_evidence: bool,
        usage_remaining: int | None,
        requires_user_confirmation: bool = False,
    ) -> GeminiCallDecision:
        cache_key = self.build_analysis_cache_key(identity)
        if requires_user_confirmation:
            return GeminiCallDecision(
                allowed=False,
                reason="user_confirmation_required",
                cache_key=cache_key,
            )
        if not has_sufficient_evidence:
            return GeminiCallDecision(
                allowed=False,
                reason="insufficient_evidence",
                cache_key=cache_key,
            )
        if usage_remaining is not None and usage_remaining <= 0:
            return GeminiCallDecision(
                allowed=False,
                reason="usage_limit_exceeded",
                cache_key=cache_key,
            )
        return GeminiCallDecision(allowed=True, reason="allowed", cache_key=cache_key)
