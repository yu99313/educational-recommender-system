import type { SurveyQuestion } from "../types";

interface Props {
  question: SurveyQuestion;
  value?: number;
  onChange: (value: number) => void;
}

export function LikertQuestion({ question, value, onChange }: Props) {
  return (
    <div className="question-card">
      <div className="question-meta">
        <span className="pill">{question.scale}</span>
        <span>{question.subscale}</span>
        <span>문항 {question.item_number}</span>
      </div>
      <p className="question-text">{question.text}</p>
      <div className="likert">
        {[1, 2, 3, 4, 5].map((score) => (
          <label key={score}>
            <input
              type="radio"
              name={question.question_id}
              checked={value === score}
              onChange={() => onChange(score)}
            />
            {score}
          </label>
        ))}
      </div>
    </div>
  );
}
