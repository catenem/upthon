import React, { useState, useEffect } from 'react';
import { getErrorMessage } from '../../services/api';
import { getDashboardStats, getDashboardItems } from '../../services/dashboard';
import type { DashboardData, DashboardItem } from '../../types/api';
import { useAlert } from '../../components/Alerts';
import * as S from './style';

import SvgBars from '../../assets/bars.svg'
import SvgSent from '../../assets/sent.svg'
import SvgClock from '../../assets/clock.svg'

// -----------------------------------------------------------------------------
// 2. COMPONENTE PRINCIPAL
// -----------------------------------------------------------------------------

const PAGE_SIZE = 100;

export function Dashboard() {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedChannel, setSelectedChannel] = useState<string>('ALL');

    const [rows, setRows] = useState<DashboardItem[]>([]);
    const [rowsTotal, setRowsTotal] = useState(0);
    const [loadingRows, setLoadingRows] = useState(false);

    const { mostrarAlerta } = useAlert();

    // A tabela é paginada: carrega PAGE_SIZE linhas por vez (do canal escolhido ou de todos).
    const loadRows = async (channel: string, offset: number) => {
        setLoadingRows(true);
        try {
            const page = await getDashboardItems(channel, offset, PAGE_SIZE);
            setRows(prev => (offset === 0 ? page.items : [...prev, ...page.items]));
            setRowsTotal(page.total);
        } catch (err) {
            mostrarAlerta(getErrorMessage(err, 'Erro ao carregar a lista de arquivos.'), 'warning');
        } finally {
            setLoadingRows(false);
        }
    };

    useEffect(() => {
        loadRows(selectedChannel, 0);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedChannel]);

    const loadDashboardStats = async () => {
        setLoading(true);
        try {
            setDashboardData(await getDashboardStats());
        } catch (err) {
            mostrarAlerta(getErrorMessage(err, 'Erro ao carregar estatísticas do dashboard.'), 'warning');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDashboardStats();
    }, []);

    if (loading) {
        return (
            <S.Container>
                <h1>Dashboard de Uploads</h1>
                <p>A carregar dados dos ficheiros...</p>
            </S.Container>
        );
    }

    if (!dashboardData) {
        return (
            <S.Container>
                <h1>Dashboard de Uploads</h1>
                <p>Nenhuma estatística disponível no momento.</p>
            </S.Container>
        );
    }

    const { overall_stats, channels, total_channels } = dashboardData;

    const singleChannelData = selectedChannel !== 'ALL'
        ? channels.find(c => c.channel_id === selectedChannel)
        : null;

    const activeSummary = singleChannelData
        ? {
            total_items: singleChannelData.total_items,
            total_sent: singleChannelData.sent_items,
            total_pending: singleChannelData.pending_items,
            progress_percentage: singleChannelData.progress_percentage
          }
        : overall_stats;

    const fileList = rows;

    return (
        <S.Container>
            <S.HeaderSection>
                <h1>Dashboard</h1>
                <S.FilterBox>
                    <select
                        id="channel-select"
                        value={selectedChannel}
                        onChange={(e) => setSelectedChannel(e.target.value)}
                    >
                        <option value="ALL">Todos os Canais ({total_channels})</option>
                        {channels.map((channel) => (
                            <option key={channel.channel_id} value={channel.channel_id}>
                                Canal ID: {channel.channel_id}
                            </option>
                        ))}
                    </select>
                </S.FilterBox>
            </S.HeaderSection>

            <h2>Estatísticas de upload</h2>
            {/* SEÇÃO 1: Cards com Resumo (Atualizam dinamicamente de acordo com a seleção) */}
            {/* SEÇÃO 1: Cards com Resumo de Progresso e Métricas */}
            <S.SummaryGrid>
                
                {/* CARD 1: Porcentagem Concluída */}
                <S.Card className='bars'>
                    <div>
                        <p className="value success">
                            {activeSummary.progress_percentage}%
                        </p>
                        <h3>Foi concluído</h3>
                    </div>
                    
                    <div className='bars'>
                        <img src={SvgBars} alt="image" />
                    </div>
                </S.Card>

                {/* CARD 2: Contador de Arquivos Upados */}
                <S.Card className='sent'>
                    <div>
                        <p className="value">
                            {activeSummary.total_sent}
                        </p>
                        <h3>Arquivos foram upados</h3>
                    </div>
                    <div className='sent'>
                        <img src={SvgSent} alt="image" />
                    </div>
                    
                </S.Card>

                {/* CARD 3: Contador de Arquivos Restantes */}
                <S.Card className='clock'>
                    <div>
                        <p className="value warning">
                            {activeSummary.total_pending}
                        </p>
                        <h3>Restantes</h3>
                    </div>
                    <div className='clock'>
                        <img src={SvgClock} alt="image" />
                    </div>
                    
                </S.Card>

            </S.SummaryGrid>

            {/* SEÇÃO 2: Barra de Progresso */}
            <S.ProgressSection>
                <h2>Historico de upload</h2>

                <S.TableContainer>
                    <S.Table>
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Tipo</th>
                                <th>Nome</th>
                            </tr>
                        </thead>
                        <tbody>
                            {fileList.map((file, index) => {
                                // Encadeamento opcional (?.) evita o erro de 'undefined' ao chamar .toUpperCase()
                                const fileExtension = file.file_name.includes('.') 
                                    ? file.file_name.split('.').pop()?.toUpperCase() ?? 'N/A'
                                    : 'N/A';

                                return (
                                    <tr key={`${file.channel_id}-${index}`}>
                                        <td className={`status-cell ${file.sent ? 'sent' : 'not-sent'}`}>
                                            <S.StatusBadge isSent={file.sent}>
                                                {file.sent ? 'Enviado' : 'Pendente'}
                                            </S.StatusBadge>
                                        </td>
                                        <td className="file-type">{fileExtension}</td>
                                        <td className="file-name">{file.file_name}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </S.Table>
                </S.TableContainer>
                {fileList.length < rowsTotal && (
                    <button type="button" disabled={loadingRows} onClick={() => loadRows(selectedChannel, fileList.length)}>
                        {loadingRows ? 'Carregando...' : `Mostrar mais (${fileList.length} de ${rowsTotal})`}
                    </button>
                )}
            </S.ProgressSection>
        </S.Container>
    );
}