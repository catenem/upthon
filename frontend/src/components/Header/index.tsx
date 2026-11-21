import React, { useState, useEffect } from 'react';
import { getCurrentUser } from '../../services/auth';
import { HeaderContainer } from './style';
import { DropDownButton } from './style';
import { DropDownContent } from './style';
import { Nav } from '../Nav';

import logoSvg from '../../assets/logo.svg';
import defaultAvatar from '../../assets/profile.svg';


export function Header() {
    const [userPhoto, setUserPhoto] = useState<string | null>(null);
    const [userName, setUserName] = useState<string | null>(null);
    useEffect(() => {
        async function loadUserData() {
            try {
                const user = await getCurrentUser();
                if (user.photo) setUserPhoto(user.photo);
                if (user.name) setUserName(user.name);
            } catch (err) {
                console.error("Erro ao carregar dados do usuário", err);
            }
        }
        loadUserData();
    }, []);

    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

    const toggleSidebar = () => setIsSidebarOpen(prev => !prev);
    const toggleUserMenu = () => setIsUserMenuOpen(prev => !prev);

    return (
        <HeaderContainer isMenuOpen={isSidebarOpen}>
            <div className='box-logo'>
                <img src={logoSvg} alt="Logo" />
                <button className='btn-menu' onClick={toggleSidebar}>
                    <svg width="9" height="18" viewBox="0 0 9 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M5 14V4L0 9L5 14ZM7 18H9V0H7V18Z" fill="white"/>
                    </svg>
                </button>
            </div>
            <div className='box-user'>
                <div className='profile'>
                    <img src={ userPhoto || defaultAvatar } alt="Profile" />
                    <p>{ userName || <a href='/login' className='login'>Fazer login</a> }</p>
                </div>
                <DropDownButton isMenuOpen={isSidebarOpen} isOpen={isUserMenuOpen}>
                    <button onClick={toggleUserMenu}>
                        <svg width="12" height="8" viewBox="0 0 12 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M6 7.4L0 1.4L1.4 0L6 4.6L10.6 0L12 1.4L6 7.4Z" fill="#708499"/>
                        </svg>
                    </button>
                </DropDownButton>
                <DropDownContent isMenuOpen={isSidebarOpen} isOpen={isUserMenuOpen}>
                    {/* Ícone de adicionar conta */}
                </DropDownContent>
            </div>
            <Nav isMenuOpen={isSidebarOpen}/>
        </HeaderContainer>
    );
};