import React from "react";
import { Link, useLocation } from "react-router-dom";
import { createPageUrl } from "@/utils";
import { Compass, BookOpen, User, LogOut } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";

const navigationItems = [
  {
    title: "Create Pathway",
    url: "/",
    icon: Compass,
  },
  {
    title: "My Pathways",
    url: "/mypathways",
    icon: BookOpen,
  },
];

export default function Layout({ children }) {
  const location = useLocation();
  const [user, setUser] = React.useState(null);

  // Simulate logged-in state using localStorage (optional)
  React.useEffect(() => {
    const savedUser = JSON.parse(localStorage.getItem("user"));
    if (savedUser) {
      setUser(savedUser);
    } else {
      // default guest user
      setUser({ full_name: "Guest User", email: "guest@example.com" });
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <SidebarProvider>
      <style>
        {`
          :root {
            --primary: 221 83% 20%;
            --primary-foreground: 210 40% 98%;
            --accent: 43 96% 56%;
            --accent-foreground: 26 83% 14%;
          }
        `}
      </style>

      <div className="min-h-screen flex w-full bg-gradient-to-br from-slate-50 via-white to-blue-50">
        <Sidebar className="border-r border-slate-200/60 bg-white/80 backdrop-blur-sm">
          <SidebarHeader className="border-b border-slate-200/60 p-6">
            <div className="flex items-center gap-3">
              <img src="./ElevatePath_logo_flat.png" alt="ElevatePath logo" />
              {/* <div className="w-10 h-10 bg-gradient-to-br from-blue-900 to-blue-700 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20">
                <Compass className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <h2 className="font-bold text-xl text-slate-900 tracking-tight">
                  ElevatePath
                </h2>
                <p className="text-xs text-slate-500 font-medium">
                  Find Your Academic Journey
                </p>
              </div> */}
            </div>
          </SidebarHeader>

          <SidebarContent className="p-3">
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navigationItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton
                        className={`hover:bg-blue-50 hover:text-blue-900 transition-all duration-200 rounded-xl mb-1.5 ${
                          location.pathname === item.url
                            ? "bg-blue-50 text-blue-900 font-semibold"
                            : "text-slate-600"
                        }`}
                      >
                        <Link
                          to={item.url}
                          className="flex items-center gap-3 px-4 py-3 w-full text-left"
                        >
                          <item.icon className="w-5 h-5" />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="border-t border-slate-200/60 p-4">
            {user ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3 px-2">
                  <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-500 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-amber-900" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-900 text-sm truncate">
                      {user.full_name}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {user.email}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="flex flex-row justify-center items-center w-full text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign Out
                </Button>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setUser({ full_name: "Guest User", email: "guest@example.com" })
                }
                className="flex flex-row justify-center items-center w-full text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer"
              >
                Sign In
              </Button>
            )}
          </SidebarFooter>
        </Sidebar>

        <main className="flex-1 flex flex-col">
          <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200/60 px-6 py-4 md:hidden">
            <div className="flex items-center gap-4">
              <SidebarTrigger className="hover:bg-slate-100 p-2 rounded-lg transition-colors duration-200" />
              <h1 className="text-xl font-bold text-slate-900">Pathway</h1>
            </div>
          </header>

          <div className="flex-1 overflow-auto">{children}</div>
        </main>
      </div>
    </SidebarProvider>
  );
}
