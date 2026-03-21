import React, { useState } from 'react';
import { 
    SettingsHeader, SettingsSection, SettingsPanel, SettingsRow,
    ToggleControl, ActionButton, InfoButton
} from '../components/SettingsUI';

export default function GeneralSettings({ navigate }) {
    const [autoUpdate, setAutoUpdate] = useState(true);
    const [offlineMode, setOfflineMode] = useState(false);
    const [notifications, setNotifications] = useState(true);

    return (
        <div className="max-w-[700px] mx-auto px-5 pb-16">
            <SettingsHeader title="General" onBack={() => navigate('dashboard')} />

            <div className="animate-in fade-in slide-in-from-bottom-[5px] duration-500 ease-out">
                <SettingsSection title="System">
                    <SettingsPanel>
                        <SettingsRow 
                            label="Automatically install updates"
                            sublabel="When enabled, your system will auto-update in the background."
                            control={<ToggleControl active={autoUpdate} onChange={setAutoUpdate} />}
                        />
                        <SettingsRow 
                            label="Offline Mode"
                            sublabel="Preserve data and prevent external network access."
                            control={<ToggleControl active={offlineMode} onChange={setOfflineMode} />}
                        />
                        <SettingsRow 
                            label="Desktop Notifications"
                            isLast={true}
                            control={<ToggleControl active={notifications} onChange={setNotifications} />}
                        />
                    </SettingsPanel>
                </SettingsSection>
                
                <SettingsSection title="Storage & Backup">
                    <SettingsPanel>
                        <SettingsRow 
                            label="Clear Application Cache"
                            isLast={true}
                            control={<ActionButton onClick={() => alert("Cleared")}>Clear Now</ActionButton>}
                        />
                    </SettingsPanel>
                </SettingsSection>
            </div>
        </div>
    );
}
