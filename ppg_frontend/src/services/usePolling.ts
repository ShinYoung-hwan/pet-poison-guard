import { useEffect } from 'react';
import api from './api';

interface UsePollingProps {
  taskId: string | null;
  onCompleted: (data: any) => void;
  intervalMs?: number;
  onStatus?: (status: string) => void;
  onError?: (err: any) => void;
}

const usePolling = ({ taskId, onCompleted, intervalMs = 1000, onStatus, onError }: UsePollingProps) => {
  useEffect(() => {
    if (!taskId) return;
    let timer: ReturnType<typeof setTimeout>;
    let stopped = false;

    const poll = async () => {
      try {
        const res = await api.getTaskStatus(taskId);
        if (onStatus) onStatus(res.status);
        if (res.status === 'completed') {
          onCompleted(res.data);
          stopped = true;
        } else if (!stopped) {
          timer = setTimeout(poll, intervalMs);
        }
      } catch (err) {
        if (onError) onError(err);
        timer = setTimeout(poll, intervalMs);
      }
    };
    poll();
    return () => {
      stopped = true;
      if (timer) clearTimeout(timer);
    };
  }, [taskId, intervalMs]);
};

export default usePolling;
