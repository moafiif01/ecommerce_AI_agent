import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { addItemsToCart } from "@/lib/cart";
import { formatPrice } from "@/lib/utils";
import { Product } from "@/types";
import { Share2, Star, ShoppingCart } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

interface ProductCardProps {
  product: Product;
  size?: "default" | "compact";
}

export function ProductCard({ product, size = "default" }: ProductCardProps) {
  const [imageError, setImageError] = useState(false);
  const [isAddingToCart, setIsAddingToCart] = useState(false);

  // Add safety checks for product data
  if (!product || !product.id) {
    return (
      <Card className="h-full flex items-center justify-center p-4">
        <p className="text-sm text-muted-foreground">Product unavailable</p>
      </Card>
    );
  }

  const isCompact = size === "compact";

  const handleShare = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const shareData = {
      title: product.name,
      text: `Check out this amazing ${product.name} from ${product.brand}!`,
      url: window.location.origin + `/products/${product.id}`,
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
      // Fallback to clipboard
      try {
        await navigator.clipboard.writeText(shareData.url);
        toast("Product link copied to clipboard!");
      } catch (clipboardError) {
        toast.error("Failed to share product");
      }
    }
  };

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!product.id || !product.price) {
      toast.error("Product information incomplete");
      return;
    }

    setIsAddingToCart(true);
    try {
      await addItemsToCart([{ productId: product.id, unitPrice: product.price, quantity: 1 }]);
      toast.success(`${product.name} added to cart!`);
    } catch (error) {
      toast.error("Failed to add to cart");
      console.error("Cart error:", error);
    } finally {
      setIsAddingToCart(false);
    }
  };

  return (
    <Link href={`/products/${product.id}`}>
      <Card className="group overflow-hidden hover:shadow-lg transition-all duration-300 h-full">
        <div
          className={`relative overflow-hidden ${
            isCompact ? "aspect-[4/3]" : "aspect-square"
          }`}
        >
          <Image
            src={
              imageError
                ? "/placeholder-image.svg"
                : product.imageUrl || "/placeholder-image.svg"
            }
            alt={product.name || "Product"}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            onError={() => setImageError(true)}
          />
          {product.isOnSale && product.salePercentage && (
            <Badge
              className={`absolute top-2 left-2 bg-red-500 hover:bg-red-600 ${
                isCompact ? "text-xs" : ""
              }`}
            >
              -{product.salePercentage}%
            </Badge>
          )}
          {product.inStock === false && (
            <Badge
              variant="secondary"
              className={`absolute top-2 right-2 ${isCompact ? "text-xs" : ""}`}
            >
              Out of Stock
            </Badge>
          )}
        </div>

        <CardContent className={`space-y-2 ${isCompact ? "p-3" : "p-4"}`}>
          <div className="space-y-1">
            <h3
              className={`font-semibold line-clamp-2 group-hover:text-primary transition-colors ${
                isCompact ? "text-sm" : ""
              }`}
            >
              {product.name || "Unnamed Product"}
            </h3>
            <p
              className={`text-muted-foreground ${
                isCompact ? "text-xs" : "text-sm"
              }`}
            >
              {product.brand || "Unknown Brand"}
            </p>
          </div>

          <div className="flex items-center space-x-1">
            <Star
              className={`fill-yellow-400 text-yellow-400 ${
                isCompact ? "h-3 w-3" : "h-4 w-4"
              }`}
            />
            <span
              className={`font-medium ${isCompact ? "text-xs" : "text-sm"}`}
            >
              {product.rating || 0}
            </span>
            <span
              className={`text-muted-foreground ${
                isCompact ? "text-xs" : "text-sm"
              }`}
            >
              ({product.reviewCount || 0})
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span
              className={`font-bold ${isCompact ? "text-base" : "text-lg"}`}
            >
              {formatPrice(product.price || 0)}
            </span>
            {product.originalPrice &&
              product.originalPrice > (product.price || 0) && (
                <span
                  className={`text-muted-foreground line-through ${
                    isCompact ? "text-xs" : "text-sm"
                  }`}
                >
                  {formatPrice(product.originalPrice)}
                </span>
              )}
          </div>
        </CardContent>

        <CardFooter className={`pt-0 ${isCompact ? "p-3" : "p-4"}`}>
          <div className="flex space-x-2 w-full justify-end gap-2">
            <Button
              size={isCompact ? "sm" : "default"}
              onClick={handleAddToCart}
              disabled={isAddingToCart || product.inStock === false}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3"
            >
              <ShoppingCart className={`${isCompact ? "h-3 w-3" : "h-4 w-4"} mr-1`} />
              {isAddingToCart ? "Adding..." : "Add to Cart"}
            </Button>
            <Button
              size={isCompact ? "sm" : "default"}
              variant="outline"
              onClick={handleShare}
              className="px-3"
            >
              <Share2 className={`${isCompact ? "h-3 w-3" : "h-4 w-4"}`} />
            </Button>
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
}
