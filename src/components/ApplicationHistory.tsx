import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { CheckCircle, Package, UserCheck, Clock, AlertCircle } from "lucide-react";

interface Application {
  id: number;
  fullName: string;
  phoneNumber: string;
  dateOfBirth: string;
  status: string;
  applicationDate: string;
  idNumber?: string;
  cardArrived: boolean;
  collected: boolean;
  application_type: string;
}

interface ApplicationHistoryProps {
  officerId: number;
}

const ApplicationHistory = ({ officerId }: ApplicationHistoryProps) => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchApplications();
  }, [officerId]);

  const fetchApplications = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/officer/applications?officer_id=${officerId}`);
      if (response.ok) {
        const data = await response.json();
        setApplications(data);
      } else {
        console.error("Failed to fetch applications");
      }
    } catch (error) {
      console.error("Error fetching applications:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCardArrived = async (applicationId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/applications/${applicationId}/card-arrived`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        toast({
          title: "Card Arrival Confirmed",
          description: "ID card arrival has been recorded.",
        });
        fetchApplications(); // Refresh the list
      } else {
        toast({
          title: "Error",
          description: "Failed to update card arrival status.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error updating card arrival:", error);
      toast({
        title: "Error",
        description: "Failed to update card arrival status.",
        variant: "destructive",
      });
    }
  };

  const handleCollected = async (applicationId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/applications/${applicationId}/collected`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        toast({
          title: "Collection Confirmed",
          description: "ID card collection has been recorded.",
        });
        fetchApplications(); // Refresh the list
      } else {
        toast({
          title: "Error",
          description: "Failed to update collection status.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error updating collection status:", error);
      toast({
        title: "Error",
        description: "Failed to update collection status.",
        variant: "destructive",
      });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return <Badge variant="secondary" className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          Pending
        </Badge>;
      case "approved":
        return <Badge variant="default" className="flex items-center gap-1 bg-green-500">
          <CheckCircle className="h-3 w-3" />
          Approved
        </Badge>;
      case "rejected":
        return <Badge variant="destructive" className="flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Rejected
        </Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return <div className="text-center py-4">Loading applications...</div>;
  }

  if (applications.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-muted-foreground">No applications found.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Application History</h3>
      {applications.map((application) => (
        <Card key={application.id}>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg">{application.fullName}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Phone: {application.phoneNumber} | DOB: {application.dateOfBirth}
                </p>
                <p className="text-sm text-muted-foreground">
                  Applied: {new Date(application.applicationDate).toLocaleDateString()}
                </p>
                <p className="text-sm text-muted-foreground">
                  Type: <span className="capitalize font-medium">{application.application_type}</span>
                </p>
                {application.idNumber && (
                  <p className="text-sm font-medium text-primary">
                    ID Number: {application.idNumber}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                {getStatusBadge(application.status)}
                <Badge variant="outline" className="capitalize">
                  {application.application_type}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {application.status.toLowerCase() === "approved" && (
                <>
                  {!application.cardArrived ? (
                    <Button
                      onClick={() => handleCardArrived(application.id)}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <Package className="h-4 w-4" />
                      Card Arrived
                    </Button>
                  ) : (
                    <Badge variant="default" className="flex items-center gap-1 bg-blue-500">
                      <Package className="h-3 w-3" />
                      Card Arrived
                    </Badge>
                  )}
                  
                  {application.cardArrived && !application.collected ? (
                    <Button
                      onClick={() => handleCollected(application.id)}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <UserCheck className="h-4 w-4" />
                      Collected
                    </Button>
                  ) : application.collected ? (
                    <Badge variant="default" className="flex items-center gap-1 bg-green-600">
                      <UserCheck className="h-3 w-3" />
                      Collected
                    </Badge>
                  ) : null}
                </>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default ApplicationHistory;