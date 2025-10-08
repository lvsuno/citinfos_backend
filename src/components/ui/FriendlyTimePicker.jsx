import { useState, useEffect } from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';

const FriendlyTimePicker = ({
  value,
  onChange,
  label = "Select time",
  size = "normal", // "small" | "normal"
  showPresets = true
}) => {
  const [hours, setHours] = useState('12');
  const [minutes, setMinutes] = useState('00');
  const [period, setPeriod] = useState('PM');
  const [showCustom, setShowCustom] = useState(false);

  // Parse existing value
  useEffect(() => {
    if (value) {
      const [h, m] = value.split(':');
      const hour24 = parseInt(h);
      const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
      const periodValue = hour24 >= 12 ? 'PM' : 'AM';

      setHours(hour12.toString().padStart(2, '0'));
      setMinutes(m);
      setPeriod(periodValue);
    }
  }, [value]);

  // Update parent when time changes
  useEffect(() => {
    let hour24 = parseInt(hours);
    if (period === 'PM' && hour24 !== 12) hour24 += 12;
    if (period === 'AM' && hour24 === 12) hour24 = 0;

    const timeString = `${hour24.toString().padStart(2, '0')}:${minutes}`;
    onChange(timeString);
  }, [hours, minutes, period, onChange]);

  const presetOptions = [
    { label: '1 hour', minutes: 60 },
    { label: '4 hours', minutes: 240 },
    { label: '12 hours', minutes: 720 },
    { label: '1 day', minutes: 1440 },
    { label: '3 days', minutes: 4320 },
    { label: '1 week', minutes: 10080 }
  ];

  const handlePresetClick = (preset) => {
    const now = new Date();
    const futureTime = new Date(now.getTime() + preset.minutes * 60000);
    const timeString = `${futureTime.getHours().toString().padStart(2, '0')}:${futureTime.getMinutes().toString().padStart(2, '0')}`;
    onChange(timeString);
    setShowCustom(false);
  };

  const sizeClasses = size === "small"
    ? "text-[10px] px-2 py-1"
    : "text-sm px-3 py-2";

  return (
    <div className="space-y-2">
      {label && (
        <label className={`block font-medium text-gray-700 ${size === "small" ? "text-[11px]" : "text-sm"}`}>
          <ClockIcon className="inline h-4 w-4 mr-1" />
          {label}
        </label>
      )}

      {showPresets && (
        <div className="space-y-2">
          <div className="grid grid-cols-3 gap-2">
            {presetOptions.map((preset, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handlePresetClick(preset)}
                className={`${sizeClasses} bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-md transition-colors font-medium`}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-center">
            <button
              type="button"
              onClick={() => setShowCustom(!showCustom)}
              className={`${sizeClasses} text-gray-600 hover:text-gray-800 underline`}
            >
              {showCustom ? 'Hide custom time' : 'Set custom time'}
            </button>
          </div>
        </div>
      )}

      {(showCustom || !showPresets) && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            {/* Hours */}
            <select
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              className={`${sizeClasses} border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500`}
            >
              {Array.from({ length: 12 }, (_, i) => {
                const hour = (i + 1).toString().padStart(2, '0');
                return (
                  <option key={hour} value={hour}>
                    {hour}
                  </option>
                );
              })}
            </select>

            <span className="text-gray-500">:</span>

            {/* Minutes */}
            <select
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
              className={`${sizeClasses} border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500`}
            >
              {['00', '15', '30', '45'].map(minute => (
                <option key={minute} value={minute}>
                  {minute}
                </option>
              ))}
            </select>

            {/* AM/PM */}
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className={`${sizeClasses} border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500`}
            >
              <option value="AM">AM</option>
              <option value="PM">PM</option>
            </select>
          </div>

          {value && (
            <p className={`text-gray-600 ${size === "small" ? "text-[9px]" : "text-xs"}`}>
              Time: {new Date(`2000-01-01T${value}`).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default FriendlyTimePicker;
