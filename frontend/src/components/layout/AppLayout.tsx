import { Container, Box } from "@mui/material";
import { ReactNode } from "react";
import { Navbar } from "./Navbar";

interface Props {
  children: ReactNode;
}

export function AppLayout({ children }: Props) {
  return (
    <Box>
      <Navbar />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {children}
      </Container>
    </Box>
  );
}
