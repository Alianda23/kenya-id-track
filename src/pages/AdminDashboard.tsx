
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Check, X, User, Phone, Mail, Building } from 'lucide-react';

interface PendingOfficer {
  id: number;
  id_number: string;
  email: string;
  phone_number: string;
  full_name: string;
  station: string;
  created_at: string;
}

const AdminDashboard = () => {
  const [pendingOfficers, setPendingOfficers] = useState<PendingOfficer[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchPendingOfficers();
  }, []);

  const fetchPendingOfficers = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/officers/pending');
      const data = await response.json();
      
      if (response.ok) {
        setPendingOfficers(data.officers);
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to fetch pending officers",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (officerId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/admin/officers/${officerId}/approve`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Success",
          description: "Officer approved successfully",
        });
        // Remove approved officer from the list
        setPendingOfficers(prev => prev.filter(officer => officer.id !== officerId));
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to approve officer",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const handleReject = async (officerId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/admin/officers/${officerId}/reject`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Success",
          description: "Officer rejected",
        });
        // Remove rejected officer from the list
        setPendingOfficers(prev => prev.filter(officer => officer.id !== officerId));
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to reject officer",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-primary mb-8">Admin Dashboard</h1>
          <div className="text-center">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-primary mb-8">Admin Dashboard</h1>
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Officer Applications - Pending Approval
            </CardTitle>
            <CardDescription>
              Review and approve officer applications to grant system access
            </CardDescription>
          </CardHeader>
          <CardContent>
            {pendingOfficers.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No pending officer applications
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Officer Details</TableHead>
                      <TableHead>Contact Information</TableHead>
                      <TableHead>Station</TableHead>
                      <TableHead>Applied Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingOfficers.map((officer) => (
                      <TableRow key={officer.id}>
                        <TableCell>
                          <div className="space-y-1">
                            <div className="font-medium">{officer.full_name}</div>
                            <div className="text-sm text-muted-foreground">
                              ID: {officer.id_number}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm">
                              <Mail className="h-4 w-4" />
                              {officer.email}
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <Phone className="h-4 w-4" />
                              {officer.phone_number}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Building className="h-4 w-4" />
                            {officer.station}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {formatDate(officer.created_at)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">Pending</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => handleApprove(officer.id)}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              <Check className="h-4 w-4 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleReject(officer.id)}
                            >
                              <X className="h-4 w-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
