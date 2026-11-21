import React, { useState, useEffect } from 'react';
import { getErrorMessage } from '../../services/api';
import { addBot, listBots } from '../../services/bots';
import type { BotInfo } from '../../types/api';
import * as S from './style';

import { useAlert } from '../../components/Alerts';
import defaulBotAvatar from '../../assets/defaultBot.svg';


export function Bots() {
    const [token, setToken] = useState('');
    const [bots, setBots] = useState<BotInfo[]>([]);
    const [loading, setLoading] = useState(false);

    // Extração da função mostrarAlerta do nosso Contexto
    const { mostrarAlerta } = useAlert();

    const loadBots = async () => {
        try {
            setBots(await listBots());
        } catch (err) {
            mostrarAlerta(getErrorMessage(err, 'Erro ao carregar bots'), 'warning');
        }
    };

    useEffect(() => { loadBots(); }, []);

    const handleAddBot = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!token.trim()) {
            mostrarAlerta('Insira um token válido antes de continuar.', 'warning');
            return;
        }

        setLoading(true);
        try {
            await addBot(token);
            setToken('');
            loadBots();
            mostrarAlerta('Bot adicionado com sucesso!', 'success');
        } catch (err) {
            mostrarAlerta(getErrorMessage(err, 'Erro ao validar o token.'), 'danger');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h1>Bots</h1>
            <S.Form onSubmit={handleAddBot}>
                <label htmlFor="bot">Adicionar Bot</label>
                <div>
                <input
                    id='bot'
                    type="text"
                    placeholder="Insira o Token http do bot"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                />

                <button type="submit" disabled={loading}>
                    {loading ? 'Validando...' : 'Adicionar Bot'}
                </button>
                </div>
            </S.Form>

            <S.BotList>
                {bots.map(bot => (
                    <div key={bot.id} className="bot-card">
                        {/* O back entrega o avatar já como data URI (sem expor o token do bot) */}
                        <img
                            src={bot.avatar_url || defaulBotAvatar}
                            alt={`Avatar de @${bot.bot_username}`}
                        />
                        <div>
                            <p>@{bot.bot_username}</p>
                            {/* O token completo nunca chega ao front: só o id público do bot */}
                            <span>{bot.token_preview}</span>
                        </div>

                    </div>
                ))}
            </S.BotList>
        </div>
    );
}
