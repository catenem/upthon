import React from 'react';
import { NavContainer } from './style';
// 1. Substituímos a importação do 'Link' pelo 'NavLink'
import { NavLink } from 'react-router-dom';

import homeSvg from '../../assets/home.svg';
import dashboardSvg from '../../assets/dashboard.svg';
import settingsSvg from '../../assets/settings.svg';
import botsSvg from '../../assets/bots.svg';

interface NavProps {
    isMenuOpen: boolean;
}

export function Nav({ isMenuOpen }: NavProps) {
    return (
        <NavContainer isMenuOpen={isMenuOpen}>
            <ul>
                <li>
                    {/* 2. Atualizamos para NavLink e ajustamos o caminho para /home */}
                    <NavLink to="/home">
                        <img src={homeSvg} alt="Home" />
                        <span>Home</span>
                    </NavLink>
                </li>
                <li>
                    <NavLink to="/dashboard">
                        <img src={dashboardSvg} alt="Dashboard" />
                        <span>Dashboard</span>
                    </NavLink>
                </li>
                <li>
                    <NavLink to="/settings">
                        <img src={settingsSvg} alt="Settings" />
                        <span>Settings</span>
                    </NavLink>
                </li>
                <li>
                    <NavLink to="/bots">
                        <img src={botsSvg} alt="Bots" />
                        <span>Bots</span> 
                    </NavLink>
                </li>
            </ul>
        </NavContainer>
    );
};