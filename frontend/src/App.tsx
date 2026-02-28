import { useEffect, useMemo, useState } from "react";
import {
  fetchLLMFallbackRecommendation,
  fetchQuestions,
  fetchRecommendation,
  fetchRequestion
} from "./api";
import { LikertQuestion } from "./components/LikertQuestion";
import { RequestionModal } from "./components/RequestionModal";
import type { LLMFallbackResponse, RecommendResponse, SurveyQuestion } from "./types";

const PAGE_SIZE = 8;
type AppView = "home" | "survey";

interface UserProfile {
  name: string;
  education: string;
  age: string;
}

interface StrategyGuide {
  label: string;
  title: string;
  summary: string;
  definition: string;
  tips: string[];
}

const STRATEGY_GUIDE: Record<string, StrategyGuide> = {
  "기억전략": {
    label: "Memory",
    title: "기억전략 (Memory)",
    summary: "암기 및 복습 기법",
    definition: "학습 내용을 반복, 연상, 구조화하여 장기 기억에 정착시키는 전략입니다.",
    tips: [
      "새 단어를 주제별로 묶어 암기하세요.",
      "이미지나 상황과 연결해 연상 기억을 만드세요.",
      "하루 10분 짧은 복습을 매일 반복하세요."
    ]
  },
  "인지전략": {
    label: "Cognitive",
    title: "인지전략 (Cognitive)",
    summary: "언어 분석 및 이해 전략",
    definition: "문장 구조 분석, 요약, 반복 연습을 통해 언어를 능동적으로 처리하는 전략입니다.",
    tips: [
      "문장을 짧게 끊어 핵심 구조를 파악하세요.",
      "읽은 내용을 2~3문장으로 요약하세요.",
      "문법 패턴을 실제 예문에 적용해 연습하세요."
    ]
  },
  "보상전략": {
    label: "Compensation",
    title: "보상전략 (Compensation)",
    summary: "부족한 언어 능력 보완 전략",
    definition: "학습자가 지식의 공백이나 제한을 극복하는 데 도움을 주는 기법입니다.",
    tips: [
      "대화 중 특정 단어가 생각나지 않으면 쉬운 동의어로 표현하세요.",
      "새로운 단어나 표현이 보이면 메모하고 반복 노출하세요.",
      "몸짓, 예시, 시각 자료를 함께 써 의미를 전달하세요."
    ]
  },
  "메타인지 전략": {
    label: "Metacognitive",
    title: "메타인지전략 (Metacognitive)",
    summary: "학습 계획 및 모니터링 전략",
    definition: "학습 과정을 계획, 점검, 조절, 평가해 자기주도성을 높이는 전략입니다.",
    tips: [
      "하루 학습 목표를 구체적으로 적고 체크하세요.",
      "학습 후 무엇이 어려웠는지 기록해 다음 계획에 반영하세요.",
      "주간 단위로 성취도를 점검해 루틴을 조정하세요."
    ]
  },
  "정의적 전략": {
    label: "Affective",
    title: "정의적전략 (Affective)",
    summary: "감정 조절 및 동기 유지 전략",
    definition: "불안과 긴장을 줄이고 학습 동기를 유지하도록 감정을 관리하는 전략입니다.",
    tips: [
      "짧은 호흡 훈련으로 긴장을 완화하세요.",
      "작은 성공 경험을 기록해 자기효능감을 높이세요.",
      "학습 목표를 난이도별로 나눠 부담을 줄이세요."
    ]
  },
  "사회적 전략": {
    label: "Social",
    title: "사회전략 (Social)",
    summary: "다른 사람과의 상호작용 전략",
    definition: "질문, 협업, 피드백을 통해 상호작용 속에서 학습 효과를 높이는 전략입니다.",
    tips: [
      "스터디 파트너와 짧은 회화를 자주 시도하세요.",
      "모르는 표현은 즉시 질문하고 피드백을 받으세요.",
      "온라인 커뮤니티에서 예문을 공유하며 점검하세요."
    ]
  },
  "사회전략": {
    label: "Social",
    title: "사회전략 (Social)",
    summary: "다른 사람과의 상호작용 전략",
    definition: "질문, 협업, 피드백을 통해 상호작용 속에서 학습 효과를 높이는 전략입니다.",
    tips: [
      "스터디 파트너와 짧은 회화를 자주 시도하세요.",
      "모르는 표현은 즉시 질문하고 피드백을 받으세요.",
      "온라인 커뮤니티에서 예문을 공유하며 점검하세요."
    ]
  }
};

function App() {
  const [view, setView] = useState<AppView>("home");
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [profile, setProfile] = useState<UserProfile>({
    name: "",
    education: "",
    age: ""
  });
  const [profileSubmitted, setProfileSubmitted] = useState(false);
  const [questions, setQuestions] = useState<SurveyQuestion[]>([]);
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [llmResult, setLlmResult] = useState<LLMFallbackResponse | null>(null);
  const [showResultPage, setShowResultPage] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const [modalOpen, setModalOpen] = useState(false);
  const [requestionRound, setRequestionRound] = useState(0);
  const [requestionMax, setRequestionMax] = useState(3);
  const [requestionQs, setRequestionQs] = useState<SurveyQuestion[]>([]);
  const [requestionAnswers, setRequestionAnswers] = useState<Record<string, number>>({});
  const [usedRequestionIds, setUsedRequestionIds] = useState<string[]>([]);
  const [tieHistory, setTieHistory] = useState<Record<"EQ" | "FLA", number[]>>({
    EQ: [],
    FLA: []
  });
  const [tieNotice, setTieNotice] = useState<string | null>(null);

  const strategies = [
    { title: "기억전략 (Memory)", desc: "암기 및 복습 기법" },
    { title: "인지전략 (Cognitive)", desc: "언어 분석 및 이해 전략" },
    { title: "보상전략 (Compensation)", desc: "부족한 언어 능력 보완 전략" },
    { title: "메타인지전략 (Metacognitive)", desc: "학습 계획 및 모니터링 전략" },
    { title: "정의적전략 (Affective)", desc: "감정 조절 및 동기 유지 전략" },
    { title: "사회전략 (Social)", desc: "다른 사람과의 상호작용 전략" }
  ];

  useEffect(() => {
    fetchQuestions()
      .then((data) => setQuestions(data.questions))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const answeredCount = useMemo(
    () => questions.filter((q) => responses[q.question_id] !== undefined).length,
    [questions, responses]
  );
  const totalPages = Math.ceil(questions.length / PAGE_SIZE);
  const currentQuestions = questions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const profileValid =
    profile.name.trim().length > 0 &&
    profile.education.trim().length > 0 &&
    profile.age.trim().length > 0;

  const strategy = useMemo(() => {
    if (!result) return null;
    return STRATEGY_GUIDE[result.recommended_strategy] || null;
  }, [result]);

  const sortedEqScores = useMemo(() => {
    if (!result) return [];
    return Object.entries(result.eq_scores)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  }, [result]);

  const sortedFlaScores = useMemo(() => {
    if (!result) return [];
    return Object.entries(result.fla_scores).sort((a, b) => b[1] - a[1]).slice(0, 4);
  }, [result]);

  const submitRecommendation = async (
    currentTieHistory: Record<"EQ" | "FLA", number[]>
  ) => {
    setError(null);
    try {
      const rec = await fetchRecommendation({
        responses,
        tie_breaker_answers: currentTieHistory
      });
      setResult(rec);
      setLlmResult(null);
      setSaveMessage(null);
      if (rec.tie_triggered && requestionRound < requestionMax) {
        const req = await fetchRequestion({
          eq_subscale: rec.top_eq_subscale,
          fla_subscale: rec.top_fla_subscale,
          used_question_ids: usedRequestionIds
        });
        setRequestionMax(req.round_limit);
        setRequestionQs(req.questions);
        setRequestionAnswers({});
        setRequestionRound((n) => n + 1);
        setUsedRequestionIds((prev) => [
          ...prev,
          ...req.questions.map((q) => q.question_id)
        ]);
        setTieNotice("평가 결과가 애매합니다. 재질문이 필요합니다.");
        setShowResultPage(false);
        setModalOpen(req.questions.length > 0);
      } else if (rec.tie_triggered && requestionRound >= requestionMax) {
        const llm = await fetchLLMFallbackRecommendation({
          responses,
          tie_breaker_answers: currentTieHistory,
          user_profile: {
            name: profile.name,
            education: profile.education,
            age: profile.age
          }
        });
        setLlmResult(llm);
        setResult((prev) =>
          prev
            ? {
                ...prev,
                recommended_strategy: llm.recommended_strategy
              }
            : prev
        );
        setModalOpen(false);
        setTieNotice(null);
        setShowResultPage(true);
      } else {
        setModalOpen(false);
        setTieNotice(null);
        setShowResultPage(true);
      }
    } catch (e) {
      setError(String(e));
    }
  };

  const handleSubmit = async () => submitRecommendation(tieHistory);

  const handleRequestionSubmit = async () => {
    const eqAnswers = requestionQs
      .filter((q) => q.scale === "EQ")
      .map((q) => requestionAnswers[q.question_id]);
    const flaAnswers = requestionQs
      .filter((q) => q.scale === "FLA")
      .map((q) => requestionAnswers[q.question_id]);

    const nextTieHistory = {
      EQ: [...tieHistory.EQ, ...eqAnswers],
      FLA: [...tieHistory.FLA, ...flaAnswers]
    };
    setTieHistory(nextTieHistory);
    setTieNotice("결과가 애매합니다. 재질문을 한 번 더 시도합니다.");
    setModalOpen(false);
    await submitRecommendation(nextTieHistory);
  };

  const saveResult = () => {
    if (!result) return;
    const payload = {
      timestamp: new Date().toISOString(),
      user: profile,
      result,
      llm_fallback: llmResult
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json;charset=utf-8"
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const fileName = `result_${new Date().toISOString().replace(/[:.]/g, "")}.json`;
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
    setSaveMessage(`결과가 성공적으로 저장되었습니다. (파일: ${fileName})`);
  };

  const resetToHome = () => {
    setView("home");
    setShowResultPage(false);
    setModalOpen(false);
    setPage(0);
    setResponses({});
    setResult(null);
    setLlmResult(null);
    setTieNotice(null);
    setRequestionRound(0);
    setRequestionAnswers({});
    setRequestionQs([]);
    setUsedRequestionIds([]);
    setSaveMessage(null);
    setTieHistory({
      EQ: [],
      FLA: []
    });
  };

  const openProfileModal = () => setProfileModalOpen(true);
  const closeProfileModal = () => setProfileModalOpen(false);
  const handleProfileSubmit = () => {
    if (!profileValid) return;
    setProfileSubmitted(true);
    setProfileModalOpen(false);
    setView("survey");
  };

  if (loading) return <div className="container">질문 로딩 중...</div>;

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">EFL 학습전략 추천</div>
        <nav className="nav">
          <button
            className={view === "home" ? "nav-btn active" : "nav-btn"}
            onClick={() => setView("home")}
          >
            홈
          </button>
          <button
            className={view === "survey" ? "nav-btn active" : "nav-btn"}
            onClick={() => setView("survey")}
            disabled={!profileSubmitted}
          >
            설문
          </button>
        </nav>
      </header>

      {view === "home" && (
        <main className="container">
          <section className="hero">
            <h1>EFL 학습전략 추천 시스템</h1>
            <p>
              당신의 정서지능(EQ)과 외국어 불안감(FLA)을 분석하여
              <br />
              최적의 학습전략을 추천해드립니다.
            </p>
            <button className="start-btn" onClick={openProfileModal}>
              설문 시작하기
            </button>
          </section>

          <section className="feature-grid">
            <article className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>개인화된 추천</h3>
              <p>EQ/FLA 하위요인 점수를 기반으로 맞춤형 학습전략을 추천합니다.</p>
            </article>
            <article className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>AI 기반 분석</h3>
              <p>상관분석 기반 로직으로 추천의 정합성과 실용성을 보장합니다.</p>
            </article>
            <article className="feature-card">
              <div className="feature-icon">🔄</div>
              <h3>재질문 메커니즘</h3>
              <p>불확실한 경우 추가 질문으로 추천 정밀도를 향상시킵니다.</p>
            </article>
            <article className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>상세한 분석</h3>
              <p>추천 근거와 함께 학습 지침을 제공하여 바로 활용할 수 있습니다.</p>
            </article>
          </section>

          <section className="strategy-panel">
            <h2>6가지 학습전략</h2>
            <div className="strategy-grid">
              {strategies.map((s) => (
                <article className="strategy-card" key={s.title}>
                  <h4>{s.title}</h4>
                  <p>{s.desc}</p>
                </article>
              ))}
            </div>
          </section>
        </main>
      )}

      {view === "survey" && (
        <main className="container">
          {!showResultPage && (
            <>
              <section className="survey-head">
                <h2>설문 응답</h2>
                <p>
                  57개 축약 문항(1~5점)에 응답하면 EQ/FLA 하위영역 점수와 상관분석 기반으로
                  전략을 추천합니다.
                </p>
              </section>
              {error && <div className="error">{error}</div>}
              <div className="progress">
                응답 진행률: {answeredCount}/{questions.length}
              </div>
              <div className="question-grid">
                {currentQuestions.map((q) => (
                  <LikertQuestion
                    key={q.question_id}
                    question={q}
                    value={responses[q.question_id]}
                    onChange={(value) =>
                      setResponses((prev) => ({ ...prev, [q.question_id]: value }))
                    }
                  />
                ))}
              </div>
              <div className="actions">
                <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                  이전
                </button>
                <span>
                  {page + 1} / {totalPages}
                </span>
                <button
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                >
                  다음
                </button>
              </div>
              {tieNotice && <div className="tie-inline-notice">{tieNotice}</div>}
              <button
                className="submit"
                disabled={answeredCount < questions.length}
                onClick={handleSubmit}
              >
                분석 및 추천 받기
              </button>
            </>
          )}

          {showResultPage && result && (
            <>
              <div className="save-warning">
                💾 중요: 결과를 저장하려면 아래 "결과 저장하기" 버튼을 클릭해주세요!
              </div>
              <section className="result">
                <h2>
                  {profile.name || "사용자"}님을 위한 학습 전략은{" "}
                  <span className="strategy-highlight">
                    {result.recommended_strategy}
                    {strategy ? ` (${strategy.label})` : ""}
                  </span>
                  입니다.
                </h2>
                <p>{strategy?.summary || result.summary}</p>
                <hr />
                <h3>추천 근거</h3>
                <p>{llmResult?.reason || result.summary}</p>
                <details>
                  <summary>상세보기</summary>
                  <table>
                    <thead>
                      <tr>
                        <th>Driver</th>
                        <th>Subscale</th>
                        <th>추천 전략</th>
                        <th>상관계수</th>
                        <th>최종 점수</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.candidates.map((c) => (
                        <tr key={c.driver}>
                          <td>{c.driver}</td>
                          <td>{c.driver_subscale}</td>
                          <td>{c.strategy_subscale}</td>
                          <td>{c.correlation.toFixed(3)}</td>
                          <td>{c.final_score.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
                <hr />
                <h3>학습지침</h3>
                <p className="guide-title">{strategy?.title || result.recommended_strategy}</p>
                <p>{strategy?.definition}</p>
                <h4>구체적인 방법:</h4>
                <ul>
                  {(strategy?.tips || []).map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
                <hr />
                <h3>전체 전략 순위</h3>
                <ol>
                  {result.strategy_ranking.map((item) => (
                    <li key={item.strategy_subscale}>
                      {item.strategy_subscale} ({item.score.toFixed(3)})
                    </li>
                  ))}
                </ol>
              </section>

              <section className="result profile-section">
                <h2>나의 학습 심리 프로필</h2>
                <div className="profile-grid">
                  <div className="profile-card eq">
                    <h4>나의 정서적 강점 (EQ)</h4>
                    {sortedEqScores.map(([name, score]) => (
                      <div className="score-row" key={name}>
                        <span>{name}</span>
                        <div className="score-track">
                          <div className="score-fill eq" style={{ width: `${(score / 5) * 100}%` }} />
                        </div>
                        <span className="score-num">{score.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="profile-card fla">
                    <h4>나의 학습 불안 요인 (FLA)</h4>
                    {sortedFlaScores.map(([name, score]) => (
                      <div className="score-row" key={name}>
                        <span>{name}</span>
                        <div className="score-track">
                          <div className="score-fill fla" style={{ width: `${(score / 5) * 100}%` }} />
                        </div>
                        <span className="score-num">{score.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              {saveMessage && <div className="save-success">{saveMessage}</div>}
              <div className="result-actions">
                <button className="save-btn" onClick={saveResult}>
                  💾 결과 저장하기
                </button>
                <button className="home-btn" onClick={resetToHome}>
                  홈으로
                </button>
              </div>
            </>
          )}
        </main>
      )}

      {profileModalOpen && (
        <div className="modal-overlay">
          <div className="profile-modal">
            <div className="profile-head">
              <h3>사용자 정보 입력</h3>
              <button className="close-btn" onClick={closeProfileModal}>
                ×
              </button>
            </div>
            <div className="profile-body">
              <label>
                이름 *
                <input
                  value={profile.name}
                  onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))}
                  placeholder="이름을 입력하세요"
                />
              </label>
              <label>
                학력 *(예: 고졸, 대학교 재학, 대학교 졸업 등)
                <input
                  value={profile.education}
                  onChange={(e) =>
                    setProfile((p) => ({ ...p, education: e.target.value }))
                  }
                  placeholder="학력을 입력하세요"
                />
              </label>
              <label>
                (만)나이 *
                <input
                  value={profile.age}
                  onChange={(e) => setProfile((p) => ({ ...p, age: e.target.value }))}
                  placeholder="만 나이를 입력하세요"
                />
              </label>
            </div>
            <div className="profile-actions">
              <button className="ghost-btn" onClick={closeProfileModal}>
                취소
              </button>
              <button className="start-btn small" onClick={handleProfileSubmit} disabled={!profileValid}>
                다음
              </button>
            </div>
          </div>
        </div>
      )}

      <RequestionModal
        open={modalOpen}
        round={requestionRound}
        maxRounds={requestionMax}
        questions={requestionQs}
        answers={requestionAnswers}
        warningText={tieNotice || undefined}
        onAnswer={(id, value) =>
          setRequestionAnswers((prev) => ({ ...prev, [id]: value }))
        }
        onSubmit={handleRequestionSubmit}
      />
    </div>
  );
}

export default App;
