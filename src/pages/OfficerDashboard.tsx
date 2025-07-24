import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LogOut, User, FileText, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

const OfficerDashboard = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [officerData, setOfficerData] = useState<any>(null);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("officerToken");
    const storedOfficerData = localStorage.getItem("officerData");
    
    if (!token || !storedOfficerData) {
      navigate("/officer");
      return;
    }

    try {
      setOfficerData(JSON.parse(storedOfficerData));
    } catch (error) {
      console.error("Error parsing officer data:", error);
      navigate("/officer");
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("officerToken");
    localStorage.removeItem("officerData");
    toast({
      title: "Logged Out",
      description: "You have been successfully logged out.",
    });
    navigate("/officer");
  };

  if (!officerData) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Officer Dashboard</h1>
            <p className="text-muted-foreground">Digital ID Management System</p>
          </div>
          <Button variant="outline" onClick={handleLogout} className="flex items-center gap-2">
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>

        {/* Welcome Section */}
        <div className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Welcome, {officerData.fullName}
              </CardTitle>
              <CardDescription>
                Station: {officerData.station} | Status: {officerData.status}
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Dashboard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                New Application
              </CardTitle>
              <CardDescription>
                Process new ID applications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">Start New Application</Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Pending Applications
              </CardTitle>
              <CardDescription>
                View applications in progress
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">View Pending</Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Application History
              </CardTitle>
              <CardDescription>
                View completed applications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">View History</Button>
            </CardContent>
          </Card>
        </div>

        {/* Quick Stats */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Quick Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-primary">0</div>
                <div className="text-sm text-muted-foreground">Today's Applications</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-primary">0</div>
                <div className="text-sm text-muted-foreground">This Week</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-primary">0</div>
                <div className="text-sm text-muted-foreground">This Month</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-primary">0</div>
                <div className="text-sm text-muted-foreground">Total Processed</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OfficerDashboard;