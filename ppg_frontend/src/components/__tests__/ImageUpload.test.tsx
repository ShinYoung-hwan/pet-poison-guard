/**
 * ImageUpload 컴포넌트 유닛 테스트
 * - 파일 선택 시 preview 렌더링 확인
 * - 업로드 성공 시 onTaskId 호출 확인
 * - 서버가 taskId를 반환하지 않을 때 오류 메시지 확인
 * - 업로드 실패(예외) 시 오류 메시지 확인
 */

import { fireEvent, waitFor } from '@testing-library/react';
import { render } from '../../__tests__/test-utils';
import ImageUpload from '../ImageUpload';
import api from '../../services/api';

jest.mock('../../services/api');

describe('ImageUpload 컴포넌트', () => {
  const mockedApi = api as jest.Mocked<typeof api>;
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;

  beforeAll(() => {
    // 테스트에서 Blob -> preview URL을 고정값으로 사용
    (URL.createObjectURL as unknown) = jest.fn(() => 'blob:http://localhost/preview');
    (URL.revokeObjectURL as unknown) = jest.fn();
  });

  afterAll(() => {
    // 원복
    (URL.createObjectURL as unknown) = originalCreateObjectURL;
    (URL.revokeObjectURL as unknown) = originalRevokeObjectURL;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('파일 선택 시 미리보기 표시 및 업로드 성공 시 onTaskId 호출', async () => {
    const onTaskId = jest.fn();
    const file = new File(['dummy'], 'food.png', { type: 'image/png' });

    mockedApi.uploadImage.mockResolvedValueOnce({ taskId: 'task-123' } as any);

    const { container, getByAltText, getByLabelText } = render(<ImageUpload onTaskId={onTaskId} />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeTruthy();

    // 파일 선택 이벤트 트리거
    fireEvent.change(input, { target: { files: [file] } });

    // preview 이미지 렌더링 대기
    await waitFor(() => expect(getByAltText('업로드된 음식 이미지 미리보기')).toBeInTheDocument());

    // api.uploadImage가 파일로 호출되었는지 확인
    expect(mockedApi.uploadImage).toHaveBeenCalledTimes(1);
    const calledWith = (mockedApi.uploadImage.mock.calls[0] || [])[0];
    expect(calledWith).toBeInstanceOf(File);
    expect((calledWith as File).name).toBe('food.png');

    // onTaskId가 호출될 때까지 대기
    await waitFor(() => expect(onTaskId).toHaveBeenCalledWith('task-123'));

    // 업로드 버튼(aria-label: 이미지 업로드)이 비활성화 상태가 아닌지 확인 (최종)
    const button = getByLabelText('이미지 업로드') as HTMLButtonElement;
    expect(button.disabled).toBe(false);
  });

  test('서버가 taskId를 반환하지 않으면 에러 메시지 표시', async () => {
    const onTaskId = jest.fn();
    const file = new File(['dummy'], 'food2.png', { type: 'image/png' });

    // 응답은 성공하지만 taskId 없음
    mockedApi.uploadImage.mockResolvedValueOnce({} as any);

    const { container, findByText } = render(<ImageUpload onTaskId={onTaskId} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    // 한글로 작성된 서버 에러 메시지 확인
    const errText = await findByText('서버에서 taskId를 반환하지 않았습니다.');
    expect(errText).toBeInTheDocument();
    expect(onTaskId).not.toHaveBeenCalled();
  });

  test('업로드 실패 시 예외 메시지 표시', async () => {
    const onTaskId = jest.fn();
    const file = new File(['dummy'], 'food3.png', { type: 'image/png' });

    mockedApi.uploadImage.mockRejectedValueOnce(new Error('network error'));

    const { container, findByText } = render(<ImageUpload onTaskId={onTaskId} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    const errNode = await findByText(/Failed to analyze image/);
    expect(errNode).toBeInTheDocument();
    expect(errNode.textContent).toMatch(/network error/);
    expect(onTaskId).not.toHaveBeenCalled();
  });
});
