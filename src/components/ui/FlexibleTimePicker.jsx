import { useState, useEffect, useRef } from 'react';
import { ClockIcon} from '@heroicons/react/24/outline';
import StyledSelect from './StyledSelect';

const FlexibleTimePicker = ({
  onDateTimeChange,
  initialDate = '',
  initialTime = '',
  size = "normal" // "small" | "normal"
}) => {
  const [date, setDate] = useState('');
  const [hours, setHours] = useState('12');
  const [minutes, setMinutes] = useState('00');
  const [period, setPeriod] = useState('PM');
  const [isInitializing, setIsInitializing] = useState(true);

  // Use ref to avoid dependency issues with onDateTimeChange
  const onDateTimeChangeRef = useRef(onDateTimeChange);
  const lastNotifiedRef = useRef('');

  // Keep the ref updated
  useEffect(() => {
    onDateTimeChangeRef.current = onDateTimeChange;
  }, [onDateTimeChange]);

  // Initialize with the provided values - respond to prop changes but prevent loops
  useEffect(() => {
    setIsInitializing(true); // Start initializing

    // Set date
    if (initialDate) {
      setDate(initialDate);
    } else {
      setDate(new Date().toISOString().split('T')[0]);
    }

    // Set time
    if (initialTime) {
      const [h, m] = initialTime.split(':');
      const hour24 = parseInt(h);
      const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
      const periodValue = hour24 >= 12 ? 'PM' : 'AM';

      // Use exact minutes value from database
      const minuteValue = parseInt(m);

      setHours(hour12.toString());
      setMinutes(minuteValue.toString().padStart(2, '0'));
      setPeriod(periodValue);
    } else {
      // Set default to current time + 1 hour
      const now = new Date();
      now.setHours(now.getHours() + 1);
      const hour24 = now.getHours();
      const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
      const periodValue = hour24 >= 12 ? 'PM' : 'AM';

      setHours(hour12.toString());
      setMinutes('00');
      setPeriod(periodValue);
    }

    // Use setTimeout to end initialization after state updates
    setTimeout(() => {
      setIsInitializing(false);
    }, 0);
  }, [initialDate, initialTime]); // Respond to prop changes

  // Only notify parent when state actually changes AND we're not initializing
  useEffect(() => {
    if (isInitializing || !date || !hours || !minutes) return;

    let hour24 = parseInt(hours);
    if (period === 'PM' && hour24 !== 12) hour24 += 12;
    if (period === 'AM' && hour24 === 12) hour24 = 0;

    const timeString = `${hour24.toString().padStart(2, '0')}:${minutes}`;
    const dateTimeKey = `${date}|${timeString}`;

    // Only notify if the datetime actually changed
    if (lastNotifiedRef.current !== dateTimeKey && onDateTimeChangeRef.current) {
      lastNotifiedRef.current = dateTimeKey;
      onDateTimeChangeRef.current(date, timeString);
    }
  }, [date, hours, minutes, period, isInitializing]);

  // Increment/Decrement functions
  const adjustDate = (days) => {
    // Create a proper local date from the date string
    const [year, month, day] = (date || new Date().toISOString().split('T')[0]).split('-');
    const currentDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));

    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + days);

    const today = new Date();
    today.setHours(0, 0, 0, 0); // Set to start of today

    // Only allow dates from today onwards
    if (newDate >= today) {
      setDate(newDate.toISOString().split('T')[0]);
    }
  };

  const adjustMinutes = (increment) => {
    const current = parseInt(minutes);
    let newMinutes = current + increment;

    // Handle overflow/underflow
    if (newMinutes >= 60) {
      newMinutes = 0;
      // Optionally increment hour here if needed
    }
    if (newMinutes < 0) {
      newMinutes = 59;
      // Optionally decrement hour here if needed
    }

    setMinutes(newMinutes.toString().padStart(2, '0'));
  };

  const quickSet = (hoursFromNow) => {
    const now = new Date();
    const future = new Date(now.getTime() + hoursFromNow * 60 * 60 * 1000);
    setDate(future.toISOString().split('T')[0]);

    const hour24 = future.getHours();
    const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
    const periodValue = hour24 >= 12 ? 'PM' : 'AM';

    setHours(hour12.toString());
    setMinutes(future.getMinutes().toString().padStart(2, '0'));
    setPeriod(periodValue);
  };

  const sizeClasses = size === "small"
    ? {
        button: "w-6 h-6 text-[10px]",
        input: "text-[10px] px-1 py-0.5 w-12",
        label: "text-[10px]",
        container: "text-[10px]"
      }
    : {
        button: "w-8 h-8 text-sm",
        input: "text-sm px-2 py-1 w-16",
        label: "text-sm",
        container: "text-sm"
      };

  return (
    <div className="space-y-3">
      <label className={`block font-medium text-gray-700 ${sizeClasses.label} flex items-center gap-1`}>
        <ClockIcon className="h-4 w-4" />
        Poll Expiration
      </label>

      {/* Main Controls Row */}
      <div className="flex items-start gap-4">
        {/* Quick Presets */}
        <div className="flex gap-1 flex-wrap">
          {[1, 4, 24, 72, 168].map(hours => (
            <button
              key={hours}
              type="button"
              onClick={() => quickSet(hours)}
              className={`${sizeClasses.button} bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded font-medium`}
              title={`${hours < 24 ? hours + 'h' : hours/24 + 'd'}`}
            >
              {hours < 24 ? hours + 'h' : hours/24 + 'd'}
            </button>
          ))}
        </div>

        {/* Date & Time Controls */}
        <div className="bg-gray-50 p-0 rounded flex items-center gap-3">
          {/* Date Row */}
          <div className="flex items-center gap-1">
            <span className={`${sizeClasses.label} text-gray-600`}>Date:</span>
            <div className="relative">
              <input
                type="date"
                value={date}
                onChange={(e) => {
                  const selectedDate = new Date(e.target.value);
                  const today = new Date();
                  today.setHours(0, 0, 0, 0);

                  // Only allow dates from today onwards
                  if (selectedDate >= today) {
                    setDate(e.target.value);
                  }
                }}
                className={`w-37 text-sm px-2 py-1 pr-6 border-gray-300 rounded focus:ring-indigo-500 focus:border-indigo-500`}
                min={new Date().toISOString().split('T')[0]}
              />
              <div className="absolute right-0 top-0 bottom-0 w-4 border-l border-gray-300 flex flex-col">
                <button
                  type="button"
                  onClick={() => adjustDate(1)}
                  className="flex-1 flex items-center justify-center bg-gray-50 hover:bg-gray-100 border-b border-gray-300 text-xs text-gray-600"
                >
                  ▲
                </button>
                <button
                  type="button"
                  onClick={() => adjustDate(-1)}
                  disabled={(() => {
                    // Create a proper local date from the date string
                    const [year, month, day] = (date || new Date().toISOString().split('T')[0]).split('-');
                    const currentDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));

                    const today = new Date();
                    today.setHours(0, 0, 0, 0);

                    // Calculate what the date would be if we subtract 1 day
                    const previousDate = new Date(currentDate);
                    previousDate.setDate(previousDate.getDate() - 1);

                    // Disable if subtracting 1 day would go before today
                    return previousDate.getTime() < today.getTime();
                  })()}
                  className="flex-1 flex items-center justify-center bg-gray-50 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed text-xs text-gray-600"
                >
                  ▼
                </button>
              </div>
            </div>
          </div>

          {/* Time Row */}
          <div className="flex items-center gap-1">
            <span className={`${sizeClasses.label} text-gray-600`}>Time:</span>

            {/* Hours */}
            <StyledSelect
              value={hours}
              onChange={(value) => setHours(value)}
              options={Array.from({length: 12}, (_, i) => ({
                value: (i + 1).toString(),
                label: (i + 1).toString().padStart(2, '0')
              }))}
              size={size === "small" ? "small" : "normal"}
              className="w-16"
            />

            <span className="text-gray-400">:</span>

            {/* Minutes */}
            <div className="relative">
              <input
                type="text"
                value={minutes}
                onChange={(e) => {
                  const value = e.target.value.replace(/[^0-9]/g, '');
                  if (value === '' || (parseInt(value) >= 0 && parseInt(value) <= 59)) {
                    setMinutes(value.padStart(2, '0'));
                  }
                }}
                className={`w-16 text-sm px-2 py-1 pr-6 border-gray-300 rounded focus:ring-indigo-500 focus:border-indigo-500 text-center`}
                placeholder="00"
                maxLength="2"
              />
              <div className="absolute right-0 top-0 bottom-0 w-4 border-l border-gray-300 flex flex-col">
                <button
                  type="button"
                  onClick={() => adjustMinutes(1)}
                  className="flex-1 flex items-center justify-center bg-gray-50 hover:bg-gray-100 border-b border-gray-300 text-xs text-gray-600"
                >
                  ▲
                </button>
                <button
                  type="button"
                  onClick={() => adjustMinutes(-1)}
                  className="flex-1 flex items-center justify-center bg-gray-50 hover:bg-gray-100 text-xs text-gray-600"
                >
                  ▼
                </button>
              </div>
            </div>

            {/* AM/PM */}
            <button
              type="button"
              onClick={() => setPeriod(period === 'AM' ? 'PM' : 'AM')}
              className={`${sizeClasses.button} px-3 bg-indigo-100 text-indigo-700 border border-indigo-300 rounded font-medium hover:bg-indigo-200 flex items-center justify-center`}
            >
              {period}
            </button>
          </div>
        </div>
      </div>

      {/* Preview */}
      {date && hours && minutes && (
        <div className="text-center p-2 bg-indigo-50 rounded">
          <p className={`text-indigo-700 font-medium ${sizeClasses.container}`}>
            ⏰ {(() => {
              try {
                // Convert 12-hour to 24-hour format
                let hour24 = parseInt(hours);
                if (period === 'PM' && hour24 !== 12) hour24 += 12;
                if (period === 'AM' && hour24 === 12) hour24 = 0;

                // Create proper date string in 24-hour format
                const dateTimeString = `${date}T${hour24.toString().padStart(2, '0')}:${minutes}:00`;
                const dateObj = new Date(dateTimeString);

                return dateObj.toLocaleString();
              } catch (error) {
                return 'Invalid date/time';
              }
            })()}
          </p>
        </div>
      )}
    </div>
  );
};

export default FlexibleTimePicker;
