import Sidebar from "./Sidebar";

export default function MainLayout({ children }) {
    return (
        <div className="flex h-screen bg-neutral-100">
            <Sidebar />
            <main className="flex-1 p-6 overflow-auto">{children}</main>
        </div>
    );
}
