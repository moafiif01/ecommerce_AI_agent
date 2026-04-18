"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/AuthContext";
import {
  cancelOrder,
  getOrderById,
  listOrders,
  trackOrder,
} from "@/lib/orders";
import { Order } from "@/types";
import { Loader2, PackageSearch, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

const CANCELLABLE_STATUSES = new Set(["processing"]);

function formatPrice(value: number) {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
  }).format(value || 0);
}

function statusVariant(status: string): "default" | "secondary" | "destructive" {
  if (status === "canceled") return "destructive";
  if (status === "delivered") return "secondary";
  return "default";
}

export default function OrdersPage() {
  const { user } = useAuth();

  const [orderNumber, setOrderNumber] = useState("");
  const [email, setEmail] = useState("");
  const [trackedOrder, setTrackedOrder] = useState<Order | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);

  const [loadingTrack, setLoadingTrack] = useState(false);
  const [loadingList, setLoadingList] = useState(false);
  const [cancelingOrderId, setCancelingOrderId] = useState<string | null>(null);

  useEffect(() => {
    if (user?.email) {
      setEmail(user.email);
    }
  }, [user]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const value = params.get("orderNumber") || "";
    if (value) {
      setOrderNumber(value.toUpperCase());
    }
  }, []);

  const canTrack = useMemo(
    () => orderNumber.trim().length > 0,
    [orderNumber],
  );

  const handleTrackOrder = async () => {
    if (!canTrack) {
      toast.error("Please enter an order number");
      return;
    }

    setLoadingTrack(true);
    try {
      const data = await trackOrder(orderNumber.trim(), email.trim() || undefined);
      if (!data.success || !data.order) {
        toast.error(data.message || "Order not found");
        setTrackedOrder(null);
        return;
      }

      setTrackedOrder(data.order);
      toast.success("Order found");
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to track order");
      setTrackedOrder(null);
    } finally {
      setLoadingTrack(false);
    }
  };

  const handleRefreshOrders = async () => {
    setLoadingList(true);
    try {
      const data = await listOrders(email.trim() || undefined, 10);
      if (!data.success) {
        toast.error(data.message || "Failed to load orders");
        setOrders([]);
        return;
      }

      setOrders(data.orders || []);
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to load orders");
      setOrders([]);
    } finally {
      setLoadingList(false);
    }
  };

  const handleLoadDetails = async (orderId: string) => {
    try {
      const data = await getOrderById(orderId);
      if (!data.success || !data.order) {
        toast.error(data.message || "Order not found");
        return;
      }

      setTrackedOrder(data.order);
      setOrderNumber(data.order.orderNumber);
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to fetch order details");
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    setCancelingOrderId(orderId);
    try {
      const data = await cancelOrder(orderId, "Canceled by customer from web portal");
      if (!data.success || !data.order) {
        toast.error(data.message || "Failed to cancel order");
        return;
      }

      setTrackedOrder((prev) => (prev?.id === orderId ? data.order! : prev));
      setOrders((prev) => prev.map((o) => (o.id === orderId ? data.order! : o)));
      toast.success("Order canceled");
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to cancel order");
    } finally {
      setCancelingOrderId(null);
    }
  };

  return (
    <div className="container py-8 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PackageSearch className="h-5 w-5" />
            Track Your Order
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <Input
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value.toUpperCase())}
              placeholder="ORD-12345678"
            />
            <Input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="customer email (optional)"
              type="email"
            />
            <Button onClick={handleTrackOrder} disabled={loadingTrack || !canTrack}>
              {loadingTrack ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Tracking...
                </>
              ) : (
                "Track order"
              )}
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={handleRefreshOrders} disabled={loadingList}>
              {loadingList ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Load recent orders
                </>
              )}
            </Button>
            <span className="text-sm text-muted-foreground self-center">
              Tip: provide your email to filter your own orders.
            </span>
          </div>
        </CardContent>
      </Card>

      {trackedOrder && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-2">
              <span>{trackedOrder.orderNumber}</span>
              <Badge variant={statusVariant(trackedOrder.status)}>
                {trackedOrder.status}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <p className="text-sm text-muted-foreground">Email</p>
                <p className="font-medium">{trackedOrder.customerEmail}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total</p>
                <p className="font-medium">{formatPrice(trackedOrder.totalAmount)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Carrier</p>
                <p className="font-medium">{trackedOrder.carrier || "-"}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Tracking #</p>
                <p className="font-medium">{trackedOrder.trackingNumber || "Pending"}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Estimated Delivery</p>
                <p className="font-medium">
                  {trackedOrder.estimatedDeliveryAt
                    ? new Date(trackedOrder.estimatedDeliveryAt).toLocaleString("fr-FR")
                    : "Not available"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Shipping Address</p>
                <p className="font-medium">{trackedOrder.shippingAddress}</p>
              </div>
            </div>

            {trackedOrder.items && trackedOrder.items.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Items</p>
                <div className="space-y-2">
                  {trackedOrder.items.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between border rounded-md px-3 py-2"
                    >
                      <p className="font-medium">{item.productName}</p>
                      <p className="text-sm text-muted-foreground">
                        x{item.quantity} - {formatPrice(item.lineTotal)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {trackedOrder.timeline && trackedOrder.timeline.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Timeline</p>
                <div className="space-y-2">
                  {[...trackedOrder.timeline].reverse().map((event, idx) => (
                    <div key={`${event.at}-${idx}`} className="border-l-2 pl-3 py-1">
                      <p className="text-sm font-medium">{event.status}</p>
                      <p className="text-sm text-muted-foreground">{event.note}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(event.at).toLocaleString("fr-FR")}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {CANCELLABLE_STATUSES.has(trackedOrder.status) && (
              <Button
                variant="destructive"
                onClick={() => handleCancelOrder(trackedOrder.id)}
                disabled={cancelingOrderId === trackedOrder.id}
              >
                {cancelingOrderId === trackedOrder.id ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Canceling...
                  </>
                ) : (
                  "Cancel order"
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent Orders</CardTitle>
        </CardHeader>
        <CardContent>
          {orders.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No orders loaded yet. Click "Load recent orders".
            </p>
          ) : (
            <div className="space-y-2">
              {orders.map((order) => (
                <div
                  key={order.id}
                  className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 border rounded-md p-3"
                >
                  <div className="space-y-1">
                    <p className="font-medium">{order.orderNumber}</p>
                    <p className="text-sm text-muted-foreground">
                      {order.customerEmail} - {formatPrice(order.totalAmount)}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={statusVariant(order.status)}>{order.status}</Badge>
                    <Button size="sm" variant="outline" onClick={() => handleLoadDetails(order.id)}>
                      View
                    </Button>
                    {CANCELLABLE_STATUSES.has(order.status) && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleCancelOrder(order.id)}
                        disabled={cancelingOrderId === order.id}
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
