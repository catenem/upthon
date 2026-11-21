import { Outlet } from 'react-router-dom';
import { Header } from '../Header';

export function DefaultLayout() {
    return (
        <>
            <Header />
            <main style={{}}>
                {/* As páginas (Home, Dash, etc) aparecem aqui */}
                <Outlet />
            </main>
        </>
    );
}