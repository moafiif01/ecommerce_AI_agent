"use client";

import { ProductGrid } from "@/components/products/ProductGrid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import api from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Product } from "@/types";
import { Share2, Star } from "lucide-react";
import Image from "next/image";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

export default function ProductDetailPage() {
  const params = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      fetchProduct();
      fetchRecommendations();
    }
  }, [params.id]);

  const fetchProduct = async () => {
    try {
      const response = await api.get(`/products/${params.id}`);
      if (response.data.success) {
        setProduct(response.data.product);
      }
    } catch (error) {
      console.error("Failed to fetch product:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await api.get("/products/recommendations", {
        params: { product_id: params.id, limit: 4 },
      });
      if (response.data.success) {
        setRecommendations(response.data.recommendations);
      }
    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
    }
  };

  const handleShare = async () => {
    if (!product) return;

    const shareData = {
      title: product.name,
      text: `Check out this amazing ${product.name} from ${product.brand}!`,
      url: window.location.href,
    };

    try {
      if (navigator.share && navigator.canShare(shareData)) {
        await navigator.share(shareData);
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(shareData.url);
        toast("Product link copied to clipboard!");
      }
    } catch (error) {
      try {
        await navigator.clipboard.writeText(shareData.url);
        toast("Product link copied to clipboard!");
      } catch (clipboardError) {
        toast.error("Failed to share product");
      }
    }
  };

  if (loading) {
    return (
      <div className="container py-8">
        <div className="animate-pulse space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="aspect-square bg-muted rounded-lg" />
            <div className="space-y-4">
              <div className="h-8 bg-muted rounded w-3/4" />
              <div className="h-4 bg-muted rounded w-1/2" />
              <div className="h-6 bg-muted rounded w-1/4" />
              <div className="h-20 bg-muted rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container py-8 text-center">
        <h1 className="text-2xl font-bold mb-4">Product Not Found</h1>
        <p className="text-muted-foreground">
          The product you're looking for doesn't exist.
        </p>
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-12">
      {/* Product Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Product Image */}
        <div className="space-y-4">
          <div className="relative aspect-square overflow-hidden rounded-lg border">
            <Image
              src={product.imageUrl}
              alt={product.name}
              fill
              className="object-cover"
              priority
            />
            {product.isOnSale && (
              <Badge className="absolute top-4 left-4 bg-red-500 hover:bg-red-600">
                -{product.salePercentage}% OFF
              </Badge>
            )}
          </div>
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">{product.name}</h1>
            <p className="text-lg text-muted-foreground">{product.brand}</p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
              <span className="font-medium">{product.rating}</span>
              <span className="text-muted-foreground">
                ({product.reviewCount} reviews)
              </span>
            </div>
            <Badge variant={product.inStock ? "default" : "secondary"}>
              {product.inStock ? "In Stock" : "Out of Stock"}
            </Badge>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <span className="text-3xl font-bold">
                {formatPrice(product.price)}
              </span>
              {product.originalPrice &&
                product.originalPrice > product.price && (
                  <span className="text-lg text-muted-foreground line-through">
                    {formatPrice(product.originalPrice)}
                  </span>
                )}
            </div>
            {product.isOnSale && (
              <p className="text-sm text-green-600">
                You save{" "}
                {formatPrice((product.originalPrice || 0) - product.price)}
              </p>
            )}
          </div>

          <p className="text-muted-foreground leading-relaxed">
            {product.description}
          </p>

          {/* Features */}
          {product.features.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">Key Features</h3>
              <ul className="space-y-1">
                {product.features.map((feature, index) => (
                  <li
                    key={index}
                    className="text-sm text-muted-foreground flex items-center"
                  >
                    <span className="w-2 h-2 bg-primary rounded-full mr-2" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Product actions */}
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-muted-foreground">
                {product.stock} available
              </span>
            </div>

            <div className="flex">
              <Button
                size="lg"
                variant="outline"
                onClick={handleShare}
                className="px-4"
              >
                <Share2 className="h-5 w-5" />
                <span className="ml-2">Share</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <Separator />

      {/* Product Details Card */}
      <Card>
        <CardHeader>
          <CardTitle>Product Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="font-medium">Category:</span>
              <span className="ml-2 text-muted-foreground">
                {product.category}
              </span>
            </div>
            <div>
              <span className="font-medium">Subcategory:</span>
              <span className="ml-2 text-muted-foreground">
                {product.subcategory}
              </span>
            </div>
            <div>
              <span className="font-medium">Brand:</span>
              <span className="ml-2 text-muted-foreground">
                {product.brand}
              </span>
            </div>
            <div>
              <span className="font-medium">Stock:</span>
              <span className="ml-2 text-muted-foreground">
                {product.stock} units
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold mb-6">You Might Also Like</h2>
          <ProductGrid products={recommendations} />
        </div>
      )}
    </div>
  );
}
