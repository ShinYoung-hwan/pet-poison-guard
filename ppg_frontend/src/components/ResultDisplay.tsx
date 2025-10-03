import React from 'react';
import PoisonResultList, { type PoisonResult } from './PoisonResultList';

interface ResultDisplayProps {
  result: PoisonResult[] | null;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result }) => {
  // TODO : 이미지 업로드 전/후를 구변해서 분석결과가 나오지 않도록 수정

  return (
    <div style={{ marginTop: 16 }}>
      <h3>분석 결과</h3>
      {
        ! result || result.length === 0 ? <p>결과가 없습니다.</p>
          : <PoisonResultList results={result} />
      }
    </div>
  );
};

export default ResultDisplay;
