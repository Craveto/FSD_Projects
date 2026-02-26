import React, { useEffect, useMemo, useState } from 'react';
import { userService } from '../services/api';
import '../styles/UserModules.css';

function UserOrdersPage({ authUser }) {
  const [orders, setOrders] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [ordersRes, deliveriesRes] = await Promise.all([
          userService.getOrders(authUser?.id),
          userService.getSubscriptionDeliveries(authUser?.id, 7),
        ]);
        setOrders(ordersRes.data || []);
        setDeliveries(deliveriesRes.data?.deliveries || []);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [authUser?.id]);

  const orderRows = useMemo(() => (
    orders.map((order) => ({
      id: order.order_id,
      status: order.status,
      total: order.total_amount,
      createdAt: order.created_at,
      items: order.items || [],
    }))
  ), [orders]);

  return (
    <div className="user-module">
      <header className="user-module-header">
        <h1>Orders</h1>
        <p>Track one-time orders and your subscription deliveries.</p>
      </header>

      {loading ? (
        <div className="module-card">Loading orders...</div>
      ) : (
        <div className="module-grid">
          <article className="module-card">
            <h3>One-Time Orders</h3>
            {orderRows.length === 0 ? (
              <div className="module-meta">No orders yet.</div>
            ) : (
              <div className="module-list">
                {orderRows.slice(0, 8).map((order) => (
                  <div key={order.id} className="module-item">
                    <div>
                      <strong>Order #{order.id}</strong>
                      <div className="module-meta">{new Date(order.createdAt).toLocaleString()}</div>
                      <div className="module-meta">{order.items.length} items</div>
                    </div>
                    <div>
                      <span className="module-badge">{order.status}</span>
                      <div className="module-meta">INR {order.total}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="module-card">
            <h3>Subscription Deliveries (Next 7 Days)</h3>
            {deliveries.length === 0 ? (
              <div className="module-meta">No subscription deliveries scheduled.</div>
            ) : (
              <div className="module-list">
                {deliveries.map((delivery) => (
                  <div key={delivery.date} className="module-item">
                    <div>
                      <strong>{new Date(delivery.date).toLocaleDateString()}</strong>
                      <div className="module-meta">
                        {(delivery.items || []).length === 0
                          ? 'No items'
                          : delivery.items.map((i) => `${i.name} x${i.quantity}`).join(', ')
                        }
                      </div>
                    </div>
                    <div>
                      <span className="module-badge">Scheduled</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>
      )}
    </div>
  );
}

export default UserOrdersPage;

