Shader "Planet/Ocean"
{
    Properties
    {
        _Deep("Deep teal", Color) = (.035,.29,.29,.96)
        _Shallow("Shelf turquoise", Color) = (.3,.63,.53,.96)
        _Wave("Height, speed, frequency", Vector) = (.24,.65,.075,0)
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Transparent" "Queue"="Transparent" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Off
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            struct A { float4 positionOS:POSITION; float4 color:COLOR; };
            struct V { float4 positionCS:SV_POSITION; float3 world:TEXCOORD0; float bed:TEXCOORD1; float fog:TEXCOORD2; };
            CBUFFER_START(UnityPerMaterial)
            float4 _Deep, _Shallow, _Wave;
            CBUFFER_END
            V Vert(A v)
            {
                V o; float3 p = TransformObjectToWorld(v.positionOS.xyz);
                p.y += _Wave.x * (sin(p.x*_Wave.z+_Time.y*_Wave.y) + .5*sin(p.z*_Wave.z*1.3-_Time.y*_Wave.y*.7));
                o.world=p; o.bed=v.color.a; o.positionCS=TransformWorldToHClip(p); o.fog=ComputeFogFactor(o.positionCS.z); return o;
            }
            half4 Frag(V i):SV_Target
            {
                float3 n=normalize(cross(ddy(i.world),ddx(i.world))); n*=sign(n.y);
                Light sun=GetMainLight(); float diffuse=saturate(dot(n,sun.direction));
                float shelf=saturate(1-(i.world.y-i.bed)/8);
                float3 col=lerp(_Deep.rgb,_Shallow.rgb,shelf)*(.68+diffuse*.32);
                float3 view=normalize(GetCameraPositionWS()-i.world);
                float glint=pow(saturate(dot(n,normalize(view+sun.direction))),180)*.32;
                float fresnel=pow(1-saturate(dot(n,view)),4);
                col=lerp(col,float3(.48,.51,.62),fresnel*.35)+glint*sun.color;
                return half4(MixFog(col,i.fog),lerp(1.0,_Deep.a,shelf));
            }
            ENDHLSL
        }
    }
}
