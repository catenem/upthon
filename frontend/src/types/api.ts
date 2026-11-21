// Tipos do contrato com o back end (espelham backend/app/schemas e as respostas dos services).
// Se o back mudar uma resposta, o erro de tipo aparece aqui e nos arquivos de src/services.

// ── Autenticação ─────────────────────────────────────────────────────────────
export interface LoginPayload {
    api_id: string;
    api_hash: string;
    phone: string;
}

export interface LoginResponse {
    status: 'awaiting_code';
    mensagem: string;
}

/** `detail` do HTTP 429 quando o Telegram bloqueia o envio do código. */
export interface RateLimitDetail {
    erro: string;
    segundos_espera: number;
    minutos_espera: number;
}

export interface VerifyPayload {
    phone: string;
    code: string;
    password?: string;
}

export interface VerifyResponse {
    status: 'needs_password' | 'success';
    mensagem: string;
}

export interface CurrentUser {
    name: string | null;
    photo: string | null; // data URI
}

// ── Arquivos ─────────────────────────────────────────────────────────────────
export interface FileNode {
    name: string;
    real_name: string;
    path: string;
    type: 'file' | 'directory';
    mp4_count?: number;
    video_count?: number;
    pdf_count?: number;
    children?: FileNode[];
    subfolders?: number;
}

// ── Uploads ──────────────────────────────────────────────────────────────────
export interface StartUploadPayload {
    channelName: string;
    typeChannel: string; // 'private' | 'topic'
    folderPath: string;
    folderName?: string;
}

export interface StartUploadResponse {
    message: string;
    channel_id: number;
}

export interface ResumeUploadPayload {
    channel_id: string;
    folderPath: string;
    is_topics?: boolean;
}

export interface ResumeUploadResponse {
    message: string;
    channel_id: string;
}

// ── Bots ─────────────────────────────────────────────────────────────────────
/** O token do bot nunca chega ao front: só um preview (o id público do bot). */
export interface BotInfo {
    id: number;
    bot_username: string;
    is_active: number;
    avatar_url: string | null; // data URI ou null
    token_preview: string;     // ex.: "123456789:…"
}

// ── Dashboard ────────────────────────────────────────────────────────────────
export interface QueueItem {
    full_path: string;
    materia: string;
    subfolder: string;
    file_name: string;
    sent: boolean;
    topic_id?: number;
}

export interface OverallStats {
    total_items: number;
    total_sent: number;
    total_pending: number;
    progress_percentage: number;
}

export interface ChannelStats {
    channel_id: string;
    file_name: string;
    total_items: number;
    sent_items: number;
    pending_items: number;
    progress_percentage: number;
    mp4_sent: number;
    mp4_pending: number;
    pdf_sent: number;
    pdf_pending: number;
    /** Só vem quando a rota é chamada com include_items=true (padrão do back). */
    items?: QueueItem[];
}

export interface DashboardData {
    total_channels: number;
    overall_stats: OverallStats;
    channels: ChannelStats[];
}

export interface DashboardItem extends QueueItem {
    channel_id: string;
}

export interface DashboardItemsPage {
    total: number;
    offset: number;
    items: DashboardItem[];
}
