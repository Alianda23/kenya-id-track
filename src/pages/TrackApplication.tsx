import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Search, ArrowLeft, FileText, Clock, CheckCircle, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

const TrackApplication = () => {
  const [waitingCardNumber, setWaitingCardNumber] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [applicationStatus, setApplicationStatus] = useState<any>(null);
  const { toast } = useToast();

  const handleSearch = async () => {
    if (!waitingCardNumber.trim()) {
      toast({
        title: "Error",
        description: "Please enter a waiting card number",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/track/${waitingCardNumber}`);
      
      if (response.ok) {
        const data = await response.json();
        setApplicationStatus(data);
      } else if (response.status === 404) {
        toast({
          title: "Not Found",
          description: "No application found with this waiting card number",
          variant: "destructive",
        });
        setApplicationStatus(null);
      } else {
        throw new Error("Failed to fetch application status");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch application status. Please try again.",
        variant: "destructive",
      });
      setApplicationStatus(null);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "approved":
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case "rejected":
        return <XCircle className="h-6 w-6 text-red-500" />;
      case "pending":
        return <Clock className="h-6 w-6 text-yellow-500" />;
      default:
        return <FileText className="h-6 w-6 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "approved":
        return "text-green-600 bg-green-50 border-green-200";
      case "rejected":
        return "text-red-600 bg-red-50 border-red-200";
      case "pending":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      default:
        return "text-muted-foreground bg-muted border-border";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Button asChild variant="ghost" className="mb-4">
            <Link to="/">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Link>
          </Button>
          
          <div className="text-center">
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Track Your Application
            </h1>
            <p className="text-muted-foreground">
              Enter your waiting card number to check your application status
            </p>
          </div>
        </div>

        <div className="max-w-2xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Application Tracker
              </CardTitle>
              <CardDescription>
                Enter the waiting card number you received when you submitted your application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="waitingCard">Waiting Card Number</Label>
                <div className="flex gap-2">
                  <Input
                    id="waitingCard"
                    type="text"
                    placeholder="Enter your waiting card number"
                    value={waitingCardNumber}
                    onChange={(e) => setWaitingCardNumber(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                  />
                  <Button 
                    onClick={handleSearch} 
                    disabled={isLoading}
                    className="px-6"
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Searching...
                      </>
                    ) : (
                      <>
                        <Search className="h-4 w-4 mr-2" />
                        Search
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {applicationStatus && (
                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Application Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-medium text-muted-foreground">
                          Applicant Name
                        </Label>
                        <p className="text-foreground font-medium">
                          {applicationStatus.firstName} {applicationStatus.lastName}
                        </p>
                      </div>
                      <div>
                        <Label className="text-sm font-medium text-muted-foreground">
                          Application Type
                        </Label>
                        <p className="text-foreground font-medium capitalize">
                          {applicationStatus.applicationType}
                        </p>
                      </div>
                      <div>
                        <Label className="text-sm font-medium text-muted-foreground">
                          Application Date
                        </Label>
                        <p className="text-foreground font-medium">
                          {new Date(applicationStatus.applicationDate).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <Label className="text-sm font-medium text-muted-foreground">
                          Current Status
                        </Label>
                        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-sm font-medium ${getStatusColor(applicationStatus.status)}`}>
                          {getStatusIcon(applicationStatus.status)}
                          <span className="capitalize">{applicationStatus.status}</span>
                        </div>
                      </div>
                    </div>
                    
                    {applicationStatus.status === "approved" && (
                      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-green-800 font-medium">
                          🎉 Congratulations! Your application has been approved.
                        </p>
                        <p className="text-green-700 text-sm mt-1">
                          You can now collect your ID from the issuing office.
                        </p>
                      </div>
                    )}
                    
                    {applicationStatus.status === "rejected" && (
                      <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-800 font-medium">
                          ❌ Your application has been rejected.
                        </p>
                        <p className="text-red-700 text-sm mt-1">
                          Please contact the issuing office for more information.
                        </p>
                      </div>
                    )}
                    
                    {applicationStatus.status === "pending" && (
                      <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-yellow-800 font-medium">
                          ⏳ Your application is currently being processed.
                        </p>
                        <p className="text-yellow-700 text-sm mt-1">
                          Please check back later for updates.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TrackApplication;