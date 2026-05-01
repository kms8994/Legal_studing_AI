"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";

type PersonaMode = "expert" | "general";
type InputMode = "text" | "pdf" | "image" | "case";

type ApiResponse<T> = {
  ok: boolean;
  data: T;
  error?: {
    message: string;
  };
};

type MermaidDiagram = {
  title: string;
  code: string;
};

type MvpAnalyzeResponse = {
  mode: string;
  input_hash: string;
  evidence_chunks: Array<{
    source_name: string;
    source_url: string;
    chunk_text: string;
  }>;
  diagrams: {
    party_relation: MermaidDiagram;
    event_timeline: MermaidDiagram;
    legal_reasoning: MermaidDiagram;
  };
  disclaimer: string;
};

type VerificationResponse = {
  status: string;
  message?: string;
};

type GeneralResponse = {
  candidates: Array<{
    title: string;
    case_number?: string;
    source_url: string;
    similarity_reason: string;
    supreme_court_holding: string;
  }>;
  limitation: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api";

const sampleText =
  "원고가 계약 해제를 주장했다. 피고는 손해배상 책임을 다투었다. 법원은 계약 해제 요건과 손해 발생 여부를 차례로 판단했다.";

export default function HomePage() {
  const [panelOpen, setPanelOpen] = useState(true);
  const [inputMode, setInputMode] = useState<InputMode>("text");
  const [personaMode, setPersonaMode] = useState<PersonaMode>("expert");
  const [text, setText] = useState(sampleText);
  const [caseNumber, setCaseNumber] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expertResult, setExpertResult] = useState<MvpAnalyzeResponse | null>(null);
  const [verification, setVerification] = useState<VerificationResponse | null>(null);
  const [generalResult, setGeneralResult] = useState<GeneralResponse | null>(null);

  const hasResult = Boolean(expertResult || generalResult);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
    script.async = true;
    script.onload = () => initializeMermaid();
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  useEffect(() => {
    renderMermaid();
  }, [expertResult]);

  const statusText = useMemo(() => {
    if (loading) return "분석 중";
    if (error) return "오류";
    if (expertResult) return "전문가 분석 완료";
    if (generalResult) return "일반인 모드 결과";
    return "대기 중";
  }, [error, expertResult, generalResult, loading]);

  async function analyze() {
    setLoading(true);
    setError("");
    setExpertResult(null);
    setGeneralResult(null);
    setVerification(null);

    try {
      const inputText = await resolveInputText();
      if (!inputText.trim()) {
        throw new Error("분석할 내용을 입력하세요.");
      }

      if (personaMode === "general") {
        const result = await post<GeneralResponse>("/general/similar-cases", {
          situation: inputText,
        });
        setGeneralResult(result);
        return;
      }

      const result = await post<MvpAnalyzeResponse>("/mvp/analyze", {
        text: inputText,
        persona_mode: "expert",
      });
      setExpertResult(result);

      try {
        const verify = await post<VerificationResponse>("/verification/check", {
          input_text: inputText,
          official_text: result.evidence_chunks[0]?.chunk_text ?? "",
          source_url: result.evidence_chunks[0]?.source_url ?? "",
        });
        setVerification(verify);
      } catch (verifyError) {
        setVerification({
          status: "unknown",
          message: verifyError instanceof Error ? verifyError.message : "검증을 완료하지 못했습니다.",
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "분석 중 문제가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function resolveInputText() {
    if (inputMode === "text") return text;
    if (inputMode === "case") {
      const result = await post<{ text: string }>("/input/case-number", {
        case_number: caseNumber,
      });
      return result.text;
    }
    if (!file) throw new Error("파일을 선택하세요.");
    const base64 = await fileToBase64(file);
    if (inputMode === "pdf") {
      const result = await post<{ text: string }>("/input/pdf", {
        filename: file.name,
        file_base64: base64,
      });
      return result.text;
    }
    const result = await post<{ extracted_text?: string; message?: string }>("/input/image", {
      mime_type: file.type,
      image_base64: base64,
    });
    if (!result.extracted_text) {
      throw new Error(result.message ?? "이미지에서 텍스트를 추출하지 못했습니다.");
    }
    return result.extracted_text;
  }

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  return (
    <main className={`app-shell ${panelOpen ? "panel-open" : "panel-closed"}`}>
      <aside className="input-panel" aria-hidden={!panelOpen}>
        <div className="panel-head">
          <div>
            <p className="eyebrow">StackSync AI</p>
            <h1>판례 분석</h1>
          </div>
          <button className="icon-button" type="button" onClick={() => setPanelOpen(false)}>
            닫기
          </button>
        </div>

        <div className="control-group">
          <label>모드</label>
          <div className="segmented">
            <button
              className={personaMode === "expert" ? "active" : ""}
              type="button"
              onClick={() => setPersonaMode("expert")}
            >
              전문가
            </button>
            <button
              className={personaMode === "general" ? "active" : ""}
              type="button"
              onClick={() => setPersonaMode("general")}
            >
              일반인
            </button>
          </div>
        </div>

        <div className="control-group">
          <label>입력</label>
          <div className="tab-grid">
            {[
              ["text", "텍스트"],
              ["pdf", "PDF"],
              ["image", "이미지"],
              ["case", "판례번호"],
            ].map(([value, label]) => (
              <button
                className={inputMode === value ? "active" : ""}
                key={value}
                type="button"
                onClick={() => {
                  setInputMode(value as InputMode);
                  setFile(null);
                }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="input-body">
          {inputMode === "text" && (
            <textarea value={text} onChange={(event) => setText(event.target.value)} />
          )}
          {inputMode === "case" && (
            <input
              placeholder="예: 2020다12345"
              value={caseNumber}
              onChange={(event) => setCaseNumber(event.target.value)}
            />
          )}
          {inputMode === "pdf" && <input accept="application/pdf" type="file" onChange={handleFile} />}
          {inputMode === "image" && <input accept="image/*" type="file" onChange={handleFile} />}
        </div>

        <button className="primary-action" disabled={loading} type="button" onClick={analyze}>
          {loading ? "분석 중..." : "분석 실행"}
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-left">
            {!panelOpen && (
              <button className="open-panel" type="button" onClick={() => setPanelOpen(true)}>
                입력 열기
              </button>
            )}
            <div>
              <p className="eyebrow">Legal RAG Workspace</p>
              <h2>분석 결과</h2>
            </div>
          </div>
          <span className={`status ${error ? "danger" : hasResult ? "ready" : ""}`}>{statusText}</span>
        </header>

        {error && <div className="error-box">{error}</div>}
        {!hasResult && !error && <EmptyState panelOpen={panelOpen} />}
        {expertResult && <ExpertView result={expertResult} verification={verification} />}
        {generalResult && <GeneralView result={generalResult} />}
      </section>
    </main>
  );
}

function ExpertView({
  result,
  verification,
}: {
  result: MvpAnalyzeResponse;
  verification: VerificationResponse | null;
}) {
  return (
    <div className="result-stack">
      <div className="metric-row">
        <InfoCard label="분석 경로" value={result.mode} />
        <InfoCard label="근거 수" value={`${result.evidence_chunks.length}개`} />
        <InfoCard label="검증 상태" value={verificationLabel(verification)} />
      </div>

      <div className="diagram-layout">
        <DiagramCard diagram={result.diagrams.party_relation} large />
        <DiagramCard diagram={result.diagrams.event_timeline} />
        <DiagramCard diagram={result.diagrams.legal_reasoning} />
      </div>

      <div className="evidence-band">
        <div>
          <h3>근거</h3>
          <p>{result.evidence_chunks[0]?.source_name ?? "근거 없음"}</p>
        </div>
        {result.evidence_chunks[0]?.source_url && (
          <a href={result.evidence_chunks[0].source_url} rel="noreferrer" target="_blank">
            원문 보기
          </a>
        )}
      </div>
      {verification?.message && <p className="verification-note">{verification.message}</p>}
      <p className="disclaimer">{result.disclaimer}</p>
    </div>
  );
}

function GeneralView({ result }: { result: GeneralResponse }) {
  return (
    <div className="general-grid">
      {result.candidates.map((candidate, index) => (
        <article className="case-card" key={`${candidate.title}-${index}`}>
          <div>
            <span className="case-number">{candidate.case_number ?? "판례 후보"}</span>
            <h3>{candidate.title}</h3>
          </div>
          <p>
            <strong>유사한 부분</strong>
            {candidate.similarity_reason}
          </p>
          <p>
            <strong>대법원 판단</strong>
            {candidate.supreme_court_holding}
          </p>
          <a href={candidate.source_url} rel="noreferrer" target="_blank">
            원문 보기
          </a>
        </article>
      ))}
      <p className="disclaimer">{result.limitation}</p>
    </div>
  );
}

function DiagramCard({ diagram, large = false }: { diagram: MermaidDiagram; large?: boolean }) {
  return (
    <article className={`diagram-card ${large ? "large" : ""}`}>
      <h3>{diagram.title}</h3>
      <pre className="mermaid">{diagram.code}</pre>
    </article>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function verificationLabel(verification: VerificationResponse | null) {
  if (!verification) return "확인 중";
  const labels: Record<string, string> = {
    valid: "검증 완료",
    modified: "변경 가능성",
    overruled: "변경 판례",
    unknown: "확인 불가",
  };
  return labels[verification.status] ?? verification.status;
}

function EmptyState({ panelOpen }: { panelOpen: boolean }) {
  return (
    <div className="empty-state">
      <p className="eyebrow">Ready</p>
      <h3>{panelOpen ? "왼쪽에서 분석을 실행하세요." : "입력 패널을 열어 사건을 입력하세요."}</h3>
      <p>
        분석 결과 영역은 다이어그램과 근거 확인에 집중하도록 넓게 구성했습니다. 입력 패널은 필요할 때만
        열고 닫을 수 있습니다.
      </p>
    </div>
  );
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const payload = (await response.json()) as ApiResponse<T>;
  if (!response.ok || payload.ok === false) {
    const detail = (payload as unknown as { detail?: unknown }).detail;
    const message =
      payload.error?.message ??
      formatApiDetail(detail) ??
      "API 요청에 실패했습니다.";
    throw new Error(message || "API 요청에 실패했습니다.");
  }
  return payload.data;
}

function formatApiDetail(detail: unknown) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object") return String(item);
        const typed = item as { loc?: unknown[]; msg?: string };
        return typed.msg ? `${typed.loc?.join(".") ?? "요청"}: ${typed.msg}` : JSON.stringify(item);
      })
      .join(" / ");
  }
  return JSON.stringify(detail);
}

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result ?? "");
      resolve(value.includes(",") ? value.split(",")[1] : value);
    };
    reader.onerror = () => reject(new Error("파일을 읽지 못했습니다."));
    reader.readAsDataURL(file);
  });
}

function initializeMermaid() {
  if (!window.mermaid) return;
  window.mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: "base",
    themeVariables: {
      background: "#111827",
      primaryTextColor: "#f8fafc",
      lineColor: "#d1d5db",
      fontFamily: "ui-sans-serif, system-ui, sans-serif",
    },
    flowchart: {
      htmlLabels: true,
      curve: "linear",
      nodeSpacing: 24,
      rankSpacing: 32,
      padding: 8,
    },
  });
}

function renderMermaid() {
  window.setTimeout(() => {
    if (!window.mermaid) return;
    window.mermaid.run({ querySelector: ".mermaid" });
  }, 0);
}

declare global {
  interface Window {
    mermaid?: {
      initialize: (config: Record<string, unknown>) => void;
      run: (config: { querySelector: string }) => Promise<void>;
    };
  }
}
