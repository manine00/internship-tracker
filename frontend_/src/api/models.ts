
export interface application {
  id: string;
  company_name: string;
  position: string;
  sent_date: any;
  email_id: string;
  status: string;
  summary: string;
}

export interface Company {
  name: string;
  internship_description: string;
  timeline: application[];
}


