import { Badge } from "@/components/ui/badge";

export function TierBadge({ tier }) {
  if (tier === "pro") return <Badge variant="pro">Pro</Badge>;
  return <Badge variant="secondary">Free</Badge>;
}
