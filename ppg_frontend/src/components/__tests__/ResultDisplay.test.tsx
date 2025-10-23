// React import not required at runtime with the current JSX transform
import { render } from '../../__tests__/test-utils';
import ResultDisplay from '../ResultDisplay';
import { screen } from '@testing-library/react';

describe('ResultDisplay 컴포넌트', () => {
  test('imageUploaded가 false면 null 반환', () => {
    const { container } = render(<ResultDisplay result={null} imageUploaded={false} />);
    expect(container.firstChild).toBeNull();
  });

  test('pollingStatus가 pending일 때 안내 표시', () => {
    render(<ResultDisplay result={null} imageUploaded={true} pollingStatus="pending" />);
    expect(screen.getByText('분석 결과')).toBeInTheDocument();
    expect(screen.getByText('분석 중입니다...')).toBeInTheDocument();
  });

  test('pollingStatus가 error일 때 에러 메시지 표시 (기본)', () => {
    render(<ResultDisplay result={null} imageUploaded={true} pollingStatus="error" />);
    expect(screen.getByText('분석 결과')).toBeInTheDocument();
    expect(screen.getByText('분석 중 오류가 발생했습니다.')).toBeInTheDocument();
  });

  test('결과가 없으면 결과 없음 메시지 표시', () => {
    render(<ResultDisplay result={[]} imageUploaded={true} pollingStatus="completed" />);
    expect(screen.getByText('결과가 없습니다.')).toBeInTheDocument();
  });

  test('결과가 있으면 리스트 컴포넌트가 렌더링된다', () => {
    const sample = [{ name: '사과', image: '/a.png', description: '사과는 안전' }];
    render(<ResultDisplay result={sample} imageUploaded={true} pollingStatus="completed" />);
    expect(screen.getByText('분석 결과')).toBeInTheDocument();
    expect(screen.getByText('사과')).toBeInTheDocument();
  });
});
