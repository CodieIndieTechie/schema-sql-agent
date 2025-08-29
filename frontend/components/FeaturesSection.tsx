
import { MessageSquare, PieChart, Zap, Lock } from "lucide-react";
import { Card, CardContent } from "./ui/card";

const FeaturesSection = () => {
  const features = [
    {
      icon: MessageSquare,
      title: "Natural Conversations",
      description: "Ask questions about your portfolio in plain English and get instant, actionable answers."
    },
    {
      icon: PieChart,
      title: "Portfolio Analytics",
      description: "Deep insights into your mutual fund performance, allocation, and risk analysis."
    },
    {
      icon: Zap,
      title: "Real-time Updates",
      description: "Stay informed with live market data and portfolio performance tracking."
    },
    {
      icon: Lock,
      title: "Secure & Private",
      description: "Your financial data is encrypted and protected with bank-level security measures."
    }
  ];

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-6xl mx-auto">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Why Choose chatfolio?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Transform how you interact with your investments through intelligent conversation and advanced analytics.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon;
              return (
                <Card key={index} className="bg-white border-gray-200 hover:shadow-lg transition-shadow duration-200">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      <div className="bg-blue-100 p-3 rounded-lg mr-4">
                        <IconComponent className="h-6 w-6 text-blue-600" />
                      </div>
                      <h3 className="text-xl font-semibold text-gray-900">
                        {feature.title}
                      </h3>
                    </div>
                    <p className="text-gray-600 leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
