// TODO: 실제 API 응답 구조에 맞게 수정
export interface AnalysisResult {
  foodName: string;
  isDangerous: boolean;
  description: string;
  dangerLevel: 'safe' | 'warning' | 'danger';
  image?: string; // 이미지 URL 또는 base64
  // 상세 설명 등 추가 필드 필요시 확장
}
