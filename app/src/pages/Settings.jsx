import React, { useState } from 'react';
import { 
    SettingsHeader, SettingsSection, SettingsPanel, SettingsRow,
    ToggleControl, SliderControl, ActionButton, InfoButton
} from '../components/SettingsUI';

export default function Settings({ navigate }) {
    const [springLoading, setSpringLoading] = useState(true);
    const [ignoreTrackpad, setIgnoreTrackpad] = useState(false);
    const [mouseKeys, setMouseKeys] = useState(false);
    const [altPointer, setAltPointer] = useState(false);
    const [headPointer, setHeadPointer] = useState(false);
    
    // Values 0 to 100
    const [doubleClickSpeed, setDoubleClickSpeed] = useState(70);
    const [springSpeed, setSpringSpeed] = useState(60);

    return (
        <div className="max-w-[700px] mx-auto px-5 pb-16">
            <SettingsHeader title="Pointer Control" onBack={() => navigate('dashboard')} />

            <div className="animate-in fade-in slide-in-from-bottom-[5px] duration-500 ease-out">
                <SettingsSection title="Mouse & Trackpad">
                    <SettingsPanel>
                        <SettingsRow 
                            label="Double-click speed"
                            control={<SliderControl value={doubleClickSpeed} onChange={setDoubleClickSpeed} />}
                        />
                        <SettingsRow 
                            label="Spring-loading"
                            control={<ToggleControl active={springLoading} onChange={setSpringLoading} />}
                        />
                        <SettingsRow 
                            label="Spring-loading speed"
                            control={<SliderControl value={springSpeed} onChange={setSpringSpeed} />}
                        />
                        <SettingsRow 
                            label="Ignore built-in trackpad when mouse or wireless trackpad is present"
                            isLast={true}
                            control={<ToggleControl active={ignoreTrackpad} onChange={setIgnoreTrackpad} />}
                        />
                    </SettingsPanel>

                    <div className="flex justify-end gap-3 mt-4 mb-8 pr-1">
                        <ActionButton>Trackpad Options...</ActionButton>
                        <ActionButton>Mouse Options...</ActionButton>
                    </div>
                </SettingsSection>

                <SettingsSection title="Alternate Control Methods">
                    <SettingsPanel>
                        <SettingsRow 
                            label="Mouse Keys"
                            sublabel="Allows the pointer to be controlled using the keyboard keys or number pad."
                            control={
                                <>
                                    <ToggleControl active={mouseKeys} onChange={setMouseKeys} />
                                    <InfoButton />
                                </>
                            }
                        />
                        <SettingsRow 
                            label="Alternate pointer actions"
                            sublabel="Allows a switch or facial expression to be used in place of mouse buttons or pointer actions like left-click and right-click."
                            control={
                                <>
                                    <ToggleControl active={altPointer} onChange={setAltPointer} />
                                    <InfoButton />
                                </>
                            }
                        />
                        <SettingsRow 
                            label="Head pointer"
                            sublabel="Allows the pointer to be controlled using the movement of your head captured by the camera."
                            isLast={true}
                            control={
                                <>
                                    <ToggleControl active={headPointer} onChange={setHeadPointer} />
                                    <InfoButton />
                                </>
                            }
                        />
                    </SettingsPanel>
                </SettingsSection>
            </div>
        </div>
    );
}
