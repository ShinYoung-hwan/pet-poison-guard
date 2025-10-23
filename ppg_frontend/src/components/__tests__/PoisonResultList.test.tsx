// React default import not required under the current JSX transform
import { render } from '../../__tests__/test-utils';
import PoisonResultList from '../PoisonResultList';
import { screen, fireEvent } from '@testing-library/react';

describe('PoisonResultList 컴포넌트', () => {
  const results = [
    { name: '바나나', image: '/banana.png', description: '바나나는 일부 동물에게 위험' },
    { name: '초콜릿', image: '/choco.png', description: '초콜릿은 매우 위험' },
  ];

  test('아이템이 순서대로 렌더링되고 이미지 대체 텍스트가 포함된다', () => {
    render(<PoisonResultList results={results} />);
    expect(screen.getByAltText('바나나')).toBeInTheDocument();
    expect(screen.getByAltText('초콜릿')).toBeInTheDocument();
    // 제목 텍스트 확인
    expect(screen.getByText('바나나')).toBeInTheDocument();
    expect(screen.getByText('초콜릿')).toBeInTheDocument();
  });

  test('아코디언을 클릭하면 상세 설명이 토글 된다', async () => {
    render(<PoisonResultList results={results} />);
    const bananaHeader = screen.getByText('바나나');
  screen.getByText('바나나는 일부 동물에게 위험');
    // Accordion의 aria-expanded 속성으로 상태 확인 (더 안정적)
    const accordion = bananaHeader.closest('[aria-expanded]');
    expect(accordion).toHaveAttribute('aria-expanded', 'false');

    // 클릭으로 열기
    fireEvent.click(bananaHeader);
    expect(accordion).toHaveAttribute('aria-expanded', 'true');

    // 다시 클릭하면 닫힘
    fireEvent.click(bananaHeader);
    expect(accordion).toHaveAttribute('aria-expanded', 'false');
  });
});
