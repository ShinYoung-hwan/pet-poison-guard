import { useEffect } from 'react';
import api from './api';

interface UsePollingProps {
  taskId: string | null;
  onCompleted: (data: any) => void;
  intervalMs?: number;
}

const usePolling = ({ taskId, onCompleted, intervalMs = 2000 }: UsePollingProps) => {
  useEffect(() => {
    if (!taskId) return;
    let timer: ReturnType<typeof setTimeout>;
    let stopped = false;

    const poll = async () => {
      try {
        const res = await api.getTaskStatus(taskId);
        if (res.status === 'completed') {
          onCompleted(res.data);
          stopped = true;
        } else if (!stopped) {
          timer = setTimeout(poll, intervalMs);
        }
      } catch {
        timer = setTimeout(poll, intervalMs);
      }
    };
    poll();
    return () => {
      stopped = true;
      if (timer) clearTimeout(timer);
    };
  }, [taskId, onCompleted, intervalMs]);
};

export default usePolling;
