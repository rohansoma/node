import React from 'react';

export function SettingsHeader({ title, onBack }) {
    return (
        <div className="flex items-center gap-3 mb-5 sticky top-0 bg-[#f2f2f7]/85 backdrop-blur-xl pb-3 pt-5 z-10 border-b border-transparent">
            {onBack && (
                <button 
                    onClick={onBack}
                    className="flex items-center text-[#007aff] hover:text-[#005bb5] transition-colors -ml-1 pr-2"
                >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M15 18l-6-6 6-6"/>
                    </svg>
                    <span className="text-[15px] font-medium ml-[-2px]">Back</span>
                </button>
            )}
            <h2 className="text-[20px] font-semibold tracking-tight text-[#000000] font-system leading-none">{title}</h2>
        </div>
    );
}

export function SettingsSection({ title, children }) {
    return (
        <div className="mb-6">
            {title && (
                <h3 className="text-[13px] font-[500] text-[#8a8a8e] mb-[6px] px-3 tracking-wide">
                    {title}
                </h3>
            )}
            <div>{children}</div>
        </div>
    );
}

export function SettingsPanel({ children, footer }) {
    return (
        <>
            <div className="bg-[#ffffff] rounded-[10px] overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.06)] border border-[#e5e5ea] mb-2 flex flex-col">
                {children}
            </div>
            {footer && (
                <div className="text-[12px] text-[#8a8a8e] px-4 mt-1.5 mb-4 leading-snug">
                    {footer}
                </div>
            )}
        </>
    );
}

export function SettingsRow({ label, sublabel, control, isLast }) {
    return (
        <div className="flex flex-col min-h-[44px]">
            <div className={`flex items-center justify-between px-4 py-2.5 flex-1`}>
                <div className="flex flex-col flex-1 pr-6 justify-center">
                    <span className="text-[15px] font-normal text-[#000000] tracking-normal mt-0.5">{label}</span>
                    {sublabel && (
                        <span className="text-[12px] font-normal text-[#8a8a8e] leading-[1.3] mt-[2px] mb-0.5">{sublabel}</span>
                    )}
                </div>
                {control && (
                    <div className="flex items-center justify-end gap-3 min-w-[120px]">
                        {control}
                    </div>
                )}
            </div>
            {!isLast && (
                <div className="ml-4 border-b border-[#e5e5ea]" />
            )}
        </div>
    );
}

export function ToggleControl({ active, onChange }) {
    return (
        <button
            onClick={() => onChange(!active)}
            className={`w-[51px] h-[31px] rounded-full relative transition-colors duration-200 ease-in-out focus:outline-none ${
                active ? 'bg-[#34c759]' : 'bg-[#e9e9ea] border border-[#d1d1d6]/50'
            }`}
        >
            <span
                className={`absolute top-[2px] left-[2px] w-[27px] h-[27px] bg-white rounded-full transition-transform duration-200 ease-in-out shadow-[0_3px_8px_rgba(0,0,0,0.15),0_1px_1px_rgba(0,0,0,0.16),0_0_0_1px_rgba(0,0,0,0.04)] ${
                    active ? 'transform translate-x-[20px]' : ''
                }`}
            />
        </button>
    );
}

export function SliderControl({ value, onChange, min = 0, max = 100 }) {
    return (
        <div className="flex items-center justify-end gap-3 w-full max-w-[220px]">
            <span className="text-[#8a8a8e] flex bg-transparent rounded p-0.5 pointer-events-none">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
            </span>
            
            <input 
                type="range"
                min={min}
                max={max}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full h-[4px] bg-[#e5e5ea] rounded-lg appearance-none cursor-pointer accent-[#007aff] outline-none"
            />

            <span className="text-[#8a8a8e] flex bg-transparent rounded p-0.5 pointer-events-none">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
            </span>
        </div>
    );
}

export function ActionButton({ children, onClick }) {
    return (
        <button
            onClick={onClick}
            className="px-3 py-1.5 bg-[#e5e5ea] hover:bg-[#d1d1d6] text-[#000000] text-[13px] font-medium rounded-md shadow-sm border border-transparent transition-colors"
        >
            {children}
        </button>
    );
}

export function InfoButton() {
    return (
        <button className="text-[#c7c7cc] hover:text-[#8a8a8e] transition-colors ml-1 flex items-center justify-center w-[20px] h-[20px] rounded-full border-[1.5px] border-current bg-white">
            <span className="text-[12px] font-bold italic pr-[1px] pb-[1px]" style={{fontFamily: "Georgia, serif"}}>i</span>
        </button>
    );
}
