import { ProductCard } from "@/components/products/ProductCard";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { formatDate } from "@/lib/utils";
import { ChatMessage as Message } from "@/types";
import { Bot, User } from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  // Add safety checks for message data
  if (!message) {
    return null;
  }

  const orderNumbers = Array.from(
    new Set((message.content || "").match(/ORD-\d{8}/g) || []),
  );

  // Metadata display helper
  const getSourceLabel = (source: string) => {
    switch (source) {
      case "order_tracking":
        return "Order Tracking";
      case "direct_support":
        return "Direct Support";
      case "guardrail":
        return "Scope Guardrail";
      case "llm":
        return "AI Assistant";
      case "groq_agent":
        return "Groq Agent";
      default:
        return "Response";
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case "order_tracking":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "direct_support":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "guardrail":
        return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200";
      case "llm":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
      case "groq_agent":
        return "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div
      className={`flex gap-3 chat-message ${
        message.isBot ? "" : "flex-row-reverse"
      }`}
    >
      <Avatar className="h-8 w-8 mt-1">
        <AvatarFallback>
          {message.isBot ? (
            <Bot className="h-4 w-4" />
          ) : (
            <User className="h-4 w-4" />
          )}
        </AvatarFallback>
      </Avatar>

      <div
        className={`flex-1 space-y-2 ${
          message.isBot ? "" : "flex flex-col items-end"
        }`}
      >
        <Card
          className={`max-w-[80%] break-words ${
            message.isBot ? "" : "bg-primary text-primary-foreground"
          }`}
        >
          <CardContent className="p-3 overflow-hidden">
            {message.isBot ? (
              <div className="text-sm prose prose-sm dark:prose-invert max-w-none break-words">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => (
                      <p className="mb-2 last:mb-0 break-words">{children}</p>
                    ),
                    ul: ({ children }) => (
                      <ul className="mb-2 ml-4 list-disc">{children}</ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="mb-2 ml-4 list-decimal">{children}</ol>
                    ),
                    li: ({ children }) => (
                      <li className="mb-1 break-words">{children}</li>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold">{children}</strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic">{children}</em>
                    ),
                    code: ({ children }) => (
                      <code className="bg-muted px-1 py-0.5 rounded text-xs break-all">
                        {children}
                      </code>
                    ),
                    pre: ({ children }) => (
                      <pre className="bg-muted p-2 rounded-md overflow-x-auto text-xs mb-2">
                        {children}
                      </pre>
                    ),
                  }}
                >
                  {message.content || ""}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm whitespace-pre-wrap break-words">
                {message.content || ""}
              </p>
            )}
            <p
              className={`text-xs mt-2 ${
                message.isBot
                  ? "text-muted-foreground"
                  : "text-primary-foreground/70"
              }`}
            >
              {message.timestamp ? formatDate(message.timestamp) : ""}
            </p>
          </CardContent>
        </Card>

        {/* Confidence Metadata Display */}
        {message.isBot && message.metadata && (
          <div className="flex flex-wrap items-center gap-2 max-w-[80%]">
            <Badge className={`${getSourceColor(message.metadata.source)} border-0`}>
              {getSourceLabel(message.metadata.source)}
            </Badge>

            {message.metadata.confidence > 0 && (
              <Badge variant="outline" className="text-xs">
                {(message.metadata.confidence * 100).toFixed(0)}% match
              </Badge>
            )}

            {message.metadata.matched_category && (
              <Badge variant="outline" className="text-xs">
                📁 {message.metadata.matched_category}
              </Badge>
            )}

            {message.metadata.matched_intent && (
              <Badge variant="outline" className="text-xs">
                🎯 {message.metadata.matched_intent}
              </Badge>
            )}

            {message.metadata.matched_question && (
              <Badge variant="outline" className="text-xs max-w-full truncate">
                🧾 {message.metadata.matched_question}
              </Badge>
            )}
          </div>
        )}

        {message.products &&
          Array.isArray(message.products) &&
          message.products.length > 0 && (
            <div className="w-full max-w-4xl">
              <ScrollArea className="w-full whitespace-nowrap">
                <div className="flex space-x-4 pb-4">
                  {message.products
                    .filter((product) => product && product.id)
                    .map((product) => (
                      <div key={product.id} className="w-56 flex-shrink-0">
                        <ErrorBoundary
                          fallback={
                            <div className="p-4 border border-gray-200 rounded-lg bg-gray-50 text-gray-600 min-h-[18rem]">
                              <p className="text-sm">
                                Product could not be loaded
                              </p>
                            </div>
                          }
                        >
                          <div className="min-h-[18rem] w-full">
                            <ProductCard product={product} size="compact" />
                          </div>
                        </ErrorBoundary>
                      </div>
                    ))}
                </div>
                <ScrollBar orientation="horizontal" />
              </ScrollArea>
            </div>
          )}

        {message.isBot && orderNumbers.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            {orderNumbers.map((orderNumber) => (
              <Button key={orderNumber} size="sm" variant="outline" asChild>
                <Link href={`/orders?orderNumber=${encodeURIComponent(orderNumber)}`}>
                  Track {orderNumber}
                </Link>
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
