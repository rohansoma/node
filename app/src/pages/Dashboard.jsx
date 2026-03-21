import React from "react";

export default function Dashboard({ navigate }) {
    return (
        <div className="px-5 py-6 max-w-[800px] mx-auto font-sans">
            <h1 className="text-[26px] font-semibold mb-6 tracking-tight text-black">Welcome</h1>
            <div className="bg-[#ffffff] rounded-xl border border-[#e5e5ea] p-6 shadow-sm mb-6">
                <h2 className="text-[14px] font-medium mb-1.5 text-black">System Status</h2>
                <p className="text-[#8a8a8e] text-[13px] mb-4">
                    All systems are running smoothly. Your custom light theme is active.
                </p>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 text-[13px] font-medium text-black/90 bg-[#f2f2f7] px-3 py-1.5 rounded-md border border-[#e5e5ea]">
                        <span className="w-2 h-2 rounded-full bg-[#34c759]"></span>
                        Online
                    </div>
                </div>
            </div>

            <div className="flex flex-col gap-4">
                <button 
                    onClick={() => navigate('general')}
                    className="bg-[#ffffff] hover:bg-[#f2f2f7] transition-colors rounded-xl border border-[#e5e5ea] p-5 text-left flex flex-col items-start gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.05)] group"
                >
                    <span className="text-[#8a8a8e] mb-1 group-hover:text-[#007aff] transition-colors">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    </span>
                    <span className="text-[14px] font-medium text-black">General</span>
                    <span className="text-[#8a8a8e] text-[12px] leading-snug">System preferences, network, and general options.</span>
                </button>

                <button 
                    onClick={() => navigate('settings')}
                    className="bg-[#ffffff] hover:bg-[#f2f2f7] transition-colors rounded-xl border border-[#e5e5ea] p-5 text-left flex flex-col items-start gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.05)] group"
                >
                    <span className="text-[#8a8a8e] mb-1 group-hover:text-[#007aff] transition-colors">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="2" width="14" height="20" rx="7"></rect><path d="M12 6v4"></path></svg>
                    </span>
                    <span className="text-[14px] font-medium text-black">Pointer Control</span>
                    <span className="text-[#8a8a8e] text-[12px] leading-snug">Configure mouse and trackpad behavior.</span>
                </button>
            </div>
        </div>
    );
}
