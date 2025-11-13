export type HealthStatus = {
  status: string;
  detail?: string | null;
  checked_at: string;
};

export type HealthResponse = {
  components: Record<string, HealthStatus>;
};

export type QueueMetrics = {
  workers: Array<{
    name: string;
    processed: Record<string, number>;
    pid: number;
    uptime: number;
    loadavg?: number[];
  }>;
  active_tasks: Record<string, number>;
  queued_tasks: Record<string, number>;
};

export type KnowledgeItemRow = {
  id: string;
  source_type: string;
  source_url: string;
  status: string;
  processed_at: string | null;
  created_at: string | null;
  last_error?: string | null;
  title?: string | null;
  has_transcript?: boolean;
};

export type KnowledgeListResponse = {
  total: number;
  items: KnowledgeItemRow[];
};
