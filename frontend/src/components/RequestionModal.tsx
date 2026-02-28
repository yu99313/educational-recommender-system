import { useMemo } from "react";
import type { SurveyQuestion } from "../types";

interface Props {
  open: boolean;
  round: number;
  maxRounds: number;
  questions: SurveyQuestion[];
  answers: Record<string, number>;
  warningText?: string;
  onAnswer: (questionId: string, value: number) => void;
  onSubmit: () => void;
}

export function RequestionModal({
  open,
  round,
  maxRounds,
  questions,
  answers,
  warningText,
  onAnswer,
  onSubmit
}: Props) {
  const isComplete = useMemo(
    () => questions.every((q) => typeof answers[q.question_id] === "number"),
    [questions, answers]
  );

  if (!open) return null;

  return (
    <div className="modal-overlay">
      <div className="requestion-modal">
        <h3>추가 질문</h3>
        <div className="requestion-warning">
          {warningText || "결과가 애매합니다. 재질문을 한번 더 시도합니다."}
        </div>
        <p className="requestion-progress-text">
          재질문: {Math.min(round, maxRounds)} / {maxRounds} 완료
        </p>
        <div className="requestion-progress-track">
          <div
            className="requestion-progress-fill"
            style={{ width: `${(Math.min(round, maxRounds) / maxRounds) * 100}%` }}
          />
        </div>
        {questions.map((q) => (
          <div className="requestion-card" key={q.question_id}>
            <div className="requestion-title">
              {q.item_number}. {q.text} ({q.scale}: {q.subscale})
            </div>
            <div className="requestion-likert">
              {[1, 2, 3, 4, 5].map((score) => (
                <label key={score} className="requestion-option">
                  <input
                    type="radio"
                    name={q.question_id}
                    checked={answers[q.question_id] === score}
                    onChange={() => onAnswer(q.question_id, score)}
                  />
                  {score}
                </label>
              ))}
            </div>
          </div>
        ))}
        <button className="requestion-submit" disabled={!isComplete} onClick={onSubmit}>
          제출하기 ({Math.min(round, maxRounds)} / {maxRounds})
        </button>
      </div>
    </div>
  );
}
