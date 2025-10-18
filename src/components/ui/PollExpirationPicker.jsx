import { useState } from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';

const PollExpirationPicker = ({
  onDateTimeChange,
  initialDate = '',
  initialTime = '',
  size = "normal" // "small" | "normal"
}) => {
  const [selectedPreset, setSelectedPreset] = useState('');
  const [showCustom, setShowCustom] = useState(false);
  const [customDate, setCustomDate] = useState(initialDate);
  const [customTime, setCustomTime] = useState(initialTime);

  const presets = [
    { id: '1h', label: '1 Heure', hours: 1 },
    { id: '4h', label: '4 Heures', hours: 4 },
    { id: '12h', label: '12 Heures', hours: 12 },
    { id: '1d', label: '1 Jour', hours: 24 },
    { id: '3d', label: '3 Jours', hours: 72 },
    { id: '1w', label: '1 Semaine', hours: 168 }
  ];

  const handlePresetSelect = (preset) => {
    const now = new Date();
    const expirationDate = new Date(now.getTime() + preset.hours * 60 * 60 * 1000);

    const date = expirationDate.toISOString().split('T')[0];
    const time = expirationDate.toTimeString().slice(0, 5);

    setSelectedPreset(preset.id);
    setShowCustom(false);
    onDateTimeChange(date, time);
  };

  const handleCustomChange = (date, time) => {
    setCustomDate(date);
    setCustomTime(time);
    setSelectedPreset('');
    onDateTimeChange(date, time);
  };

  const sizeClasses = {
    button: size === "small" ? "text-[10px] px-2 py-1" : "text-sm px-3 py-2",
    input: size === "small" ? "text-[10px] px-2 py-1" : "text-sm px-3 py-2",
    label: size === "small" ? "text-[11px]" : "text-sm"
  };

  return (
    <div className="space-y-3">
      <label className={`block font-medium text-gray-700 ${sizeClasses.label}`}>
        <ClockIcon className="inline h-4 w-4 mr-1" />
        Expiration du sondage
      </label>

      {/* Preset Duration Buttons */}
      <div className="grid grid-cols-3 gap-2">
        {presets.map((preset) => (
          <button
            key={preset.id}
            type="button"
            onClick={() => handlePresetSelect(preset)}
            className={`${sizeClasses.button} border rounded-md font-medium transition-all ${
              selectedPreset === preset.id
                ? 'bg-indigo-100 border-indigo-300 text-indigo-700'
                : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Custom Date/Time Toggle */}
      <div className="text-center">
        <button
          type="button"
          onClick={() => {
            setShowCustom(!showCustom);
            if (!showCustom) setSelectedPreset('');
          }}
          className={`${sizeClasses.button} text-gray-600 hover:text-gray-800 underline`}
        >
          {showCustom ? 'Utiliser les options rapides' : 'Définir une date et heure personnalisées'}
        </button>
      </div>

      {/* Custom Date/Time Inputs */}
      {showCustom && (
        <div className="space-y-2 p-3 bg-gray-50 rounded-md">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className={`block ${sizeClasses.label} text-gray-600 mb-1`}>Date</label>
              <input
                type="date"
                value={customDate}
                onChange={(e) => handleCustomChange(e.target.value, customTime)}
                className={`w-full ${sizeClasses.input} border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500`}
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div>
              <label className={`block ${sizeClasses.label} text-gray-600 mb-1`}>Heure</label>
              <input
                type="time"
                value={customTime}
                onChange={(e) => handleCustomChange(customDate, e.target.value)}
                className={`w-full ${sizeClasses.input} border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500`}
              />
            </div>
          </div>
        </div>
      )}

      {/* Preview */}
      {(customDate && customTime) || selectedPreset ? (
        <div className={`text-center p-2 bg-indigo-50 rounded-md`}>
          <p className={`text-indigo-700 font-medium ${size === "small" ? "text-[10px]" : "text-sm"}`}>
            📅 Expire le: {customDate && customTime
              ? new Date(`${customDate}T${customTime}`).toLocaleString()
              : selectedPreset
                ? (() => {
                    const preset = presets.find(p => p.id === selectedPreset);
                    const expDate = new Date(Date.now() + preset.hours * 60 * 60 * 1000);
                    return expDate.toLocaleString();
                  })()
                : ''
            }
          </p>
        </div>
      ) : (
        <div className={`text-center p-2 bg-yellow-50 rounded-md`}>
          <p className={`text-yellow-700 ${size === "small" ? "text-[10px]" : "text-sm"}`}>
            ⚡ Par défaut: dans 1 jour
          </p>
        </div>
      )}
    </div>
  );
};

export default PollExpirationPicker;
