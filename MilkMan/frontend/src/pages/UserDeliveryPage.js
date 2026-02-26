import React, { useEffect, useMemo, useState } from 'react';
import { userService } from '../services/api';
import '../styles/UserModules.css';

function UserDeliveryPage({ authUser }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const loadOrders = async () => {
      try {
        const response = await userService.getOrders(authUser?.id);
        setOrders(response.data || []);
      } finally {
        setLoading(false);
      }
    };
    loadOrders();
  }, [authUser?.id]);

  const upcoming = useMemo(() => (
    orders
      .filter((order) => order.status === 'paid')
      .slice(0, 5)
      .map((order, index) => ({
        id: order.order_id,
        date: new Date(new Date(order.created_at).getTime() + ((index + 1) * 24 * 60 * 60 * 1000)),
        amount: order.total_amount,
      }))
  ), [orders]);

  return (
    <div className="user-module">
      <header className="user-module-header">
        <h1>Delivery Schedule</h1>
        <p>Track upcoming deliveries and control your delivery flow.</p>
      </header>

      <div className="module-actions">
        <button type="button" onClick={() => setPaused((previous) => !previous)}>
          {paused ? 'Resume Deliveries' : 'Pause Deliveries'}
        </button>
      </div>

      {loading ? (
        <div className="module-card">Loading delivery schedule...</div>
      ) : (
        <div className="module-list">
          {upcoming.length === 0 ? (
            <div className="module-card">No paid orders yet. Deliveries will appear here.</div>
          ) : upcoming.map((item) => (
            <div key={item.id} className="module-item">
              <div>
                <strong>Order #{item.id}</strong>
                <div className="module-meta">{item.date.toLocaleString()}</div>
              </div>
              <div>
                <span className="module-badge">{paused ? 'Paused' : 'Scheduled'}</span>
                <div className="module-meta">INR {item.amount}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default UserDeliveryPage;
