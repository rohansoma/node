import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function TypographyCard({ label }) {
    return (
        <Card>
            <CardHeader>{label}</CardHeader>
            <CardContent>
                <p className="text-5xl font-semibold">Aa</p>
            </CardContent>
        </Card>
    );
}
