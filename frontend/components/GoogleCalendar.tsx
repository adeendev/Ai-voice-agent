'use client';

import React, { useState, useEffect } from 'react';

interface Booking {
  booking_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email: string;
  service_type: string;
  booking_date: string;
  booking_time: string;
  status: string;
  notes: string;
  created_at: string;
  google_calendar_event_id?: string;
}

interface CalendarEvent {
  id: string;
  summary: string;
  description: string;
  start: {
    dateTime: string;
    timeZone: string;
  };
  end: {
    dateTime: string;
    timeZone: string;
  };
  status: string;
}

interface GoogleCalendarProps {
  onBack: () => void;
  backendUrl: string;
}

export default function GoogleCalendar({ onBack, backendUrl }: GoogleCalendarProps) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [calendarStatus, setCalendarStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');

  // Fetch bookings from the API
  const fetchBookings = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/bookings`);
      if (response.ok) {
        const data = await response.json();
        setBookings(data.bookings || []);
      } else {
        throw new Error('Failed to fetch bookings');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch bookings');
    }
  };

  // Check Google Calendar status
  const checkCalendarStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/health`);
      if (response.ok) {
        const data = await response.json();
        setCalendarStatus(data.components?.google_calendar ? 'connected' : 'disconnected');
      }
    } catch (err) {
      setCalendarStatus('error');
    }
  };

  // Fetch calendar events (mock for now since we need Google Calendar API setup)
  const fetchCalendarEvents = async () => {
    try {
      // This would be a real API call to get Google Calendar events
      // For now, we'll show the bookings that have Google Calendar event IDs
      const eventsFromBookings = bookings
        .filter(booking => booking.google_calendar_event_id)
        .map(booking => ({
          id: booking.google_calendar_event_id!,
          summary: `${booking.service_type} - ${booking.customer_name}`,
          description: `Service: ${booking.service_type}\nCustomer: ${booking.customer_name}\nPhone: ${booking.customer_phone}\nNotes: ${booking.notes}`,
          start: {
            dateTime: `${booking.booking_date}T${booking.booking_time}:00`,
            timeZone: 'UTC'
          },
          end: {
            dateTime: `${booking.booking_date}T${booking.booking_time}:00`,
            timeZone: 'UTC'
          },
          status: booking.status
        }));
      
      setCalendarEvents(eventsFromBookings);
    } catch (err) {
      console.error('Failed to fetch calendar events:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchBookings(),
        checkCalendarStatus()
      ]);
      setLoading(false);
    };

    loadData();
  }, []);

  useEffect(() => {
    if (bookings.length > 0) {
      fetchCalendarEvents();
    }
  }, [bookings]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed': return 'text-green-400 bg-green-900/20';
      case 'pending': return 'text-yellow-400 bg-yellow-900/20';
      case 'cancelled': return 'text-red-400 bg-red-900/20';
      case 'completed': return 'text-blue-400 bg-blue-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const formatDateTime = (date: string, time: string) => {
    try {
      const dateTime = new Date(`${date}T${time}`);
      return dateTime.toLocaleString();
    } catch {
      return `${date} ${time}`;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
        <div className="max-w-6xl mx-auto">
          <div className="glass-panel p-8 text-center">
            <div className="text-6xl mb-4">📅</div>
            <h2 className="text-2xl font-bold text-white mb-4">Loading Calendar...</h2>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="glass-panel p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBack}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-all duration-200"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">📅 Google Calendar Integration</h1>
                <p className="text-gray-300">Manage your bookings and calendar events</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1 rounded-full text-sm ${
                calendarStatus === 'connected' 
                  ? 'bg-green-900/20 text-green-400' 
                  : calendarStatus === 'error'
                  ? 'bg-red-900/20 text-red-400'
                  : 'bg-yellow-900/20 text-yellow-400'
              }`}>
                {calendarStatus === 'connected' ? '🟢 Connected' : 
                 calendarStatus === 'error' ? '🔴 Error' : '🟡 Disconnected'}
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="glass-panel p-4 mb-6 border-l-4 border-red-500">
            <div className="flex items-center space-x-2">
              <span className="text-red-400">❌</span>
              <span className="text-white">{error}</span>
            </div>
          </div>
        )}

        {/* Calendar Status */}
        <div className="glass-panel p-6 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">📊 Calendar Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl mb-2">📅</div>
              <h3 className="text-lg font-semibold text-white">Total Bookings</h3>
              <p className="text-2xl font-bold text-blue-400">{bookings.length}</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🔗</div>
              <h3 className="text-lg font-semibold text-white">Calendar Events</h3>
              <p className="text-2xl font-bold text-green-400">{calendarEvents.length}</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">⏰</div>
              <h3 className="text-lg font-semibold text-white">Pending</h3>
              <p className="text-2xl font-bold text-yellow-400">
                {bookings.filter(b => b.status === 'pending').length}
              </p>
            </div>
          </div>
        </div>

        {/* Bookings List */}
        <div className="glass-panel p-6">
          <h2 className="text-xl font-bold text-white mb-6">📋 Recent Bookings</h2>
          
          {bookings.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📅</div>
              <h3 className="text-xl font-semibold text-white mb-2">No bookings found</h3>
              <p className="text-gray-300">Start a conversation to create your first booking!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {bookings.map((booking) => (
                <div key={booking.booking_id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">{booking.service_type}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(booking.status)}`}>
                          {booking.status.toUpperCase()}
                        </span>
                        {booking.google_calendar_event_id && (
                          <span className="px-2 py-1 rounded-full text-xs bg-green-900/20 text-green-400">
                            📅 Synced
                          </span>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-gray-300">
                            <span className="font-medium">Customer:</span> {booking.customer_name}
                          </p>
                          <p className="text-gray-300">
                            <span className="font-medium">Phone:</span> {booking.customer_phone}
                          </p>
                          {booking.customer_email && (
                            <p className="text-gray-300">
                              <span className="font-medium">Email:</span> {booking.customer_email}
                            </p>
                          )}
                        </div>
                        <div>
                          <p className="text-gray-300">
                            <span className="font-medium">Date & Time:</span> {formatDateTime(booking.booking_date, booking.booking_time)}
                          </p>
                          <p className="text-gray-300">
                            <span className="font-medium">Booking ID:</span> {booking.booking_id}
                          </p>
                          {booking.notes && (
                            <p className="text-gray-300">
                              <span className="font-medium">Notes:</span> {booking.notes}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Calendar Integration Info */}
        {calendarStatus !== 'connected' && (
          <div className="glass-panel p-6 mt-6">
            <h2 className="text-xl font-bold text-white mb-4">🔧 Google Calendar Setup</h2>
            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <span className="text-yellow-400 text-xl">⚠️</span>
                <div>
                  <h3 className="text-lg font-semibold text-yellow-400 mb-2">Calendar Integration Not Active</h3>
                  <p className="text-gray-300 mb-3">
                    To enable automatic calendar event creation, you need to authenticate with Google Calendar.
                  </p>
                  <div className="text-sm text-gray-400">
                    <p>• Bookings will still be saved to the database</p>
                    <p>• Calendar events will be created once authentication is complete</p>
                    <p>• Check the server logs for authentication instructions</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}