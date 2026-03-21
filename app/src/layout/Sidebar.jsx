import React from "react";

export default function Sidebar({ currentPath, navigate }) {
    const navItems = [
        { 
            id: 'dashboard', 
            label: 'Dashboard', 
            icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        },
        { 
            id: 'settings', 
            label: 'Pointer Control', 
            icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="2" width="14" height="20" rx="7"></rect><path d="M12 6v4"></path></svg>
        },
    ];

    return (
        <div className="w-[240px] bg-[#1c1c1e] bg-opacity-[.95] backdrop-blur-[20px] border-r border-[#38383a] p-3 flex flex-col gap-1 text-[13px] font-medium text-[#ffffff]">
            <div className="relative mb-4 mt-8 px-1">
                <input 
                    type="text" 
                    placeholder="Search" 
                    className="w-full bg-[#38383a]/60 border border-transparent rounded-md py-[5px] pl-7 pr-3 text-[13px] font-normal focus:outline-none focus:ring-2 focus:ring-[#0a84ff]/60 focus:bg-[#2c2c2e] placeholder:text-[#86868b] text-[#ffffff] transition-all"
                />
                <span className="absolute left-[10px] top-[7px] text-[#86868b]">
                    <svg width="13" height="13" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M10 6.5C10 8.433 8.433 10 6.5 10C4.567 10 3 8.433 3 6.5C3 4.567 4.567 3 6.5 3C8.433 3 10 4.567 10 6.5ZM9.30884 10.0159C8.53901 10.6318 7.56251 11 6.5 11C4.01472 11 2 8.98528 2 6.5C2 4.01472 4.01472 2 6.5 2C8.98528 2 11 4.01472 11 6.5C11 7.56251 10.6318 8.53901 10.0159 9.30884L12.8536 12.1464C13.0488 12.3417 13.0488 12.6583 12.8536 12.8536C12.6583 13.0488 12.3417 13.0488 12.1464 12.8536L9.30884 10.0159Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
                    </svg>
                </span>
            </div>
            
            <div className="px-1 mb-1 text-[11px] font-semibold text-[#86868b] tracking-normal">
                Menu
            </div>
            
            {navItems.map(item => (
                <button 
                    key={item.id}
                    onClick={() => navigate(item.id)}
                    className={`flex items-center gap-2.5 px-3 py-[5px] rounded-lg transition-colors text-left font-sans ${
                        currentPath === item.id 
                            ? 'bg-[#0a84ff] text-white shadow-[0_1px_2px_rgba(0,0,0,0.15)] font-semibold' 
                            : 'hover:bg-[#2c2c2e] text-[#dddddf] font-medium'
                    }`}
                >
                    <span className="flex items-center justify-center opacity-80">{item.icon}</span>
                    <span>{item.label}</span>
                </button>
            ))}
        </div>
    );
}
