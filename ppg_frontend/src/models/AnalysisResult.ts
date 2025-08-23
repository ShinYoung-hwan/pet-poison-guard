// TODO: 실제 API 응답 구조에 맞게 수정
export interface AnalysisResult {
  foodName: string;
  isDangerous: boolean;
  description: string;
  dangerLevel: 'safe' | 'warning' | 'danger';
}
