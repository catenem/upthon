import { api } from './api';
import type { DashboardData, DashboardItemsPage } from '../types/api';

/** Totais por canal, sem a lista de arquivos (leve mesmo com milhares de itens). */
export async function getDashboardStats(): Promise<DashboardData> {
    const res = await api.get<DashboardData>('/dashboard/stats', { params: { include_items: false } });
    return res.data;
}

/** Uma página dos arquivos de um canal (ou de todos, com channelId = 'ALL'). */
export async function getDashboardItems(channelId: string, offset: number, limit: number): Promise<DashboardItemsPage> {
    const res = await api.get<DashboardItemsPage>('/dashboard/items', {
        params: { channel_id: channelId, offset, limit },
    });
    return res.data;
}
