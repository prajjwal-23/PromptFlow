/**
 * EventStream component for real-time execution event display.
 * 
 * Premium Terminal UI implementation with dark mode, syntax highlighting feel, and modern controls.
 */

import React, { useState, useEffect, useRef } from 'react';
import { useExecutionStore } from '../../store/executionStore';
import { getWebSocketClient } from '../../websocket/client';
import { FunnelIcon, TrashIcon, MagnifyingGlassIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

interface EventStreamProps {
  executionId?: string;
  maxHeight?: string;
  showFilters?: boolean;
  className?: string;
}

type EventLevel = 'info' | 'warning' | 'error' | 'debug';
type EventType = string;

export const EventStream: React.FC<EventStreamProps> = ({
  executionId,
  maxHeight = '500px',
  showFilters = true,
  className = ''
}) => {
  const {
    events,
    currentExecution,
    websocketConnected,
    clearEvents
  } = useExecutionStore();

  const [filteredEvents, setFilteredEvents] = useState(events);
  const [selectedLevels, setSelectedLevels] = useState<Set<EventLevel>>(new Set(['info', 'warning', 'error']));
  const [selectedTypes, setSelectedTypes] = useState<Set<EventType>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());

  const eventStreamRef = useRef<HTMLDivElement>(null);
  const wsClient = getWebSocketClient();

  // Filter events based on criteria
  useEffect(() => {
    let filtered = events;

    if (executionId) {
      filtered = filtered.filter(event => event.run_id === executionId);
    }

    if (selectedLevels.size > 0) {
      filtered = filtered.filter(event => selectedLevels.has(event.level));
    }

    if (selectedTypes.size > 0) {
      filtered = filtered.filter(event => selectedTypes.has(event.event_type));
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(event =>
        event.message.toLowerCase().includes(term) ||
        event.event_type.toLowerCase().includes(term) ||
        (event.node_id && event.node_id.toLowerCase().includes(term))
      );
    }

    setFilteredEvents(filtered);
  }, [events, executionId, selectedLevels, selectedTypes, searchTerm]);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (isAutoScroll && eventStreamRef.current) {
      const scrollContainer = eventStreamRef.current;
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }, [filteredEvents, isAutoScroll]);

  const availableTypes = Array.from(new Set(events.map(event => event.event_type)));

  const toggleLevel = (level: EventLevel) => {
    const newLevels = new Set(selectedLevels);
    if (newLevels.has(level)) {
      newLevels.delete(level);
    } else {
      newLevels.add(level);
    }
    setSelectedLevels(newLevels);
  };

  const toggleType = (type: EventType) => {
    const newTypes = new Set(selectedTypes);
    if (newTypes.has(type)) {
      newTypes.delete(type);
    } else {
      newTypes.add(type);
    }
    setSelectedTypes(newTypes);
  };

  const toggleEventExpansion = (eventId: string) => {
    const newExpanded = new Set(expandedEvents);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedEvents(newExpanded);
  };

  const getLevelColor = (level: EventLevel): string => {
    switch (level) {
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      case 'info': return 'text-blue-400';
      case 'debug': return 'text-zinc-500';
      default: return 'text-zinc-400';
    }
  };

  const getLevelBadge = (level: EventLevel) => {
    const colors = {
      error: 'bg-red-500/10 text-red-400 border-red-500/20',
      warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      debug: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
    };
    return (
      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border uppercase tracking-wider ${colors[level] || colors.debug}`}>
        {level}
      </span>
    );
  };

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
  };

  const handleScroll = () => {
    if (eventStreamRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = eventStreamRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 20;
      setIsAutoScroll(isAtBottom);
    }
  };

  return (
    <div className={`flex flex-col rounded-xl border border-zinc-800 bg-zinc-950 shadow-2xl overflow-hidden ${className}`}>
      {/* Terminal Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 px-4 py-2 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-red-500/20 border border-red-500/50" />
            <div className="h-3 w-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
            <div className="h-3 w-3 rounded-full bg-green-500/20 border border-green-500/50" />
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
            <span className="text-zinc-600">~/execution-logs</span>
            {websocketConnected ? (
              <span className="flex items-center gap-1 text-emerald-500">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                LIVE
              </span>
            ) : (
              <span className="text-zinc-600">OFFLINE</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsAutoScroll(!isAutoScroll)}
            className={`px-2 py-1 text-xs rounded border transition-colors ${isAutoScroll
                ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                : 'bg-zinc-800 text-zinc-400 border-zinc-700 hover:bg-zinc-700'
              }`}
          >
            {isAutoScroll ? 'Auto-scroll: ON' : 'Auto-scroll: OFF'}
          </button>
          <button
            onClick={clearEvents}
            className="p-1.5 text-zinc-400 hover:text-red-400 transition-colors"
            title="Clear Logs"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Filters Toolbar */}
      {showFilters && (
        <div className="flex flex-wrap items-center gap-3 border-b border-zinc-800 bg-zinc-900/30 px-4 py-2">
          <div className="relative flex-1 min-w-[200px]">
            <MagnifyingGlassIcon className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              placeholder="grep events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 py-1.5 pl-9 pr-3 text-xs text-zinc-300 placeholder-zinc-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-1 border-l border-zinc-800 pl-3">
            {(['error', 'warning', 'info', 'debug'] as EventLevel[]).map(level => (
              <button
                key={level}
                onClick={() => toggleLevel(level)}
                className={`px-2 py-1 text-[10px] uppercase font-medium rounded border transition-all ${selectedLevels.has(level)
                    ? getLevelBadge(level).props.className
                    : 'bg-transparent text-zinc-600 border-transparent hover:bg-zinc-900 hover:text-zinc-400'
                  }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Log Output */}
      <div
        ref={eventStreamRef}
        className="flex-1 overflow-y-auto bg-zinc-950 p-4 font-mono text-xs scrollbar-thin scrollbar-track-zinc-950 scrollbar-thumb-zinc-800"
        style={{ maxHeight }}
        onScroll={handleScroll}
      >
        {filteredEvents.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-zinc-600">
            <p className="text-sm">No events captured</p>
            <p className="text-xs opacity-50">Waiting for execution stream...</p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredEvents.map((event, index) => (
              <div
                key={`${event.id}-${index}`}
                className={`group relative flex gap-3 rounded px-2 py-1 transition-colors hover:bg-zinc-900/50 ${expandedEvents.has(event.id) ? 'bg-zinc-900/30' : ''
                  }`}
              >
                {/* Timestamp */}
                <span className="shrink-0 text-zinc-600 select-none">
                  {formatTimestamp(event.timestamp)}
                </span>

                {/* Level Indicator */}
                <span className={`shrink-0 w-16 font-bold ${getLevelColor(event.level)}`}>
                  [{event.level.toUpperCase()}]
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-300">{event.event_type}</span>
                    {event.node_id && (
                      <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">
                        {event.node_id}
                      </span>
                    )}
                  </div>

                  <p className="mt-0.5 text-zinc-400 break-words whitespace-pre-wrap">
                    {event.message}
                  </p>

                  {/* Details Toggle */}
                  {(event.data || event.duration_ms || event.token_count) && (
                    <button
                      onClick={() => toggleEventExpansion(event.id)}
                      className="mt-1 flex items-center gap-1 text-[10px] text-zinc-500 hover:text-indigo-400"
                    >
                      {expandedEvents.has(event.id) ? (
                        <><ChevronUpIcon className="h-3 w-3" /> Hide Details</>
                      ) : (
                        <><ChevronDownIcon className="h-3 w-3" /> View Details</>
                      )}
                    </button>
                  )}

                  {/* Expanded Details */}
                  {expandedEvents.has(event.id) && (
                    <div className="mt-2 rounded border border-zinc-800 bg-zinc-950/50 p-2">
                      {event.data && (
                        <div className="mb-2">
                          <span className="text-indigo-400">Data:</span>
                          <pre className="mt-1 overflow-x-auto text-zinc-500">
                            {JSON.stringify(event.data, null, 2)}
                          </pre>
                        </div>
                      )}
                      <div className="flex gap-4 text-zinc-500">
                        {event.duration_ms && (
                          <span>Duration: <span className="text-zinc-300">{event.duration_ms}ms</span></span>
                        )}
                        {event.token_count && (
                          <span>Tokens: <span className="text-zinc-300">{event.token_count}</span></span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EventStream;