
import { Button } from "@/components/ui/button";
import { Chrome } from "lucide-react";

const AuthSection = () => {
  const handleGoogleSignIn = () => {
    // This will need Supabase integration for actual Google auth
    console.log("Google sign in clicked - requires Supabase integration");
    alert("Please connect to Supabase first to enable Google authentication. Click the green Supabase button in the top right corner.");
  };

  return (
    <section className="py-4 bg-white">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-md mx-auto text-center">
        </div>
      </div>
    </section>
  );
};

export default AuthSection;
