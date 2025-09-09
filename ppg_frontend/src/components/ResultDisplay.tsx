import React from 'react';
import PoisonResultList, { type PoisonResult } from './PoisonResultList';

interface ResultDisplayProps {
  result: PoisonResult[] | null;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result }) => {
  if (!result || result.length === 0) return null;
  return (
    <div style={{ marginTop: 16 }}>
      <h3>분석 결과</h3>
      <PoisonResultList results={result} />
    </div>
  );
};

export default ResultDisplay;
