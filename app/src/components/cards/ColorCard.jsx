import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function ColorCard({ title, color }) {
    return (
        <Card>
            <CardHeader>{title}</CardHeader>
            <CardContent>
                <div
                    className="h-16 rounded-md"
                    style={{ backgroundColor: color }}
                />
            </CardContent>
        </Card>
    );
}
